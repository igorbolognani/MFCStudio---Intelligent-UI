"""Curate commercial facts without turning specifications into calibrated MFC parameters."""
from __future__ import annotations
from decimal import Decimal
import math


class UnitError(ValueError):
    pass


# Units are quantity-specific: ASR and bulk resistivity cannot share a conversion.
UNITS = {
    'thickness': {'m': (1, 'm'), 'mm': (.001, 'm'), 'um': (1e-6, 'm')},
    'areal_mass': {'g/m2': (.001, 'kg/m2')},
    'bulk_density': {'g/cm3': (1000, 'kg/m3')},
    'porosity': {'%': (.01, '1'), '1': (1, '1')},
    'BET_specific_area': {'m2/g': (1000, 'm2/kg')},
    'electronic_resistivity': {'Ohm*m': (1, 'Ohm*m'), 'Ohm*mm': (.001, 'Ohm*m'), 'mOhm*cm': (1e-5, 'Ohm*m')},
    'electronic_ASR': {'Ohm*cm2': (1e-4, 'Ohm*m2'), 'mOhm*cm2': (1e-7, 'Ohm*m2')},
    'membrane_ASR': {'Ohm*cm2': (1e-4, 'Ohm*m2'), 'mOhm*cm2': (1e-7, 'Ohm*m2')},
    'metal_loading': {'mgPt/cm2': (.01, 'kgPt/m2')},
    'catalyst_metal_mass_fraction': {'wt%': (.01, '1')},
    'gas_transit_time': {'s': (1, 's')},
    'intrinsic_gas_permeability': {'m2': (1, 'm2'), '1e-12*m2': (1e-12, 'm2')},
    'electrolyte_conductivity': {'S/m': (1, 'S/m'), 'mS/cm': (.1, 'S/m'), 'S/cm': (100, 'S/m')},
    'permselectivity': {'%': (.01, '1')},
}
RELATIONS = {'eq', 'lt', 'le', 'gt', 'ge'}


def finite(value):
    return isinstance(value, (float, int)) and not isinstance(value, bool) and math.isfinite(value)


def normalize_property(observation):
    quantity, unit, value = (observation.get(k) for k in ('quantity', 'unit', 'value'))
    if quantity not in UNITS or unit not in UNITS[quantity]:
        raise UnitError(f'Unresolved unit for {quantity}: {unit}')
    if not finite(value) or value < 0:
        raise ValueError('Property value must be finite and nonnegative')
    if observation.get('relation') not in RELATIONS:
        raise ValueError('Preserve an explicit comparison relation')
    factor, si_unit = UNITS[quantity][unit]
    normalized = value * factor
    if si_unit == '1' and not 0 <= normalized <= 1:
        raise ValueError('Fraction outside [0,1]')
    uncertainty = observation.get('plus_minus')
    if uncertainty is not None and (not finite(uncertainty) or uncertainty < 0):
        raise ValueError('Invalid reported plus/minus value')
    return {
        'quantity': quantity, 'value': normalized, 'unit': si_unit,
        'relation': observation['relation'],
        'value_role': observation['value_role'],
        'reported_plus_minus': None if uncertainty is None else uncertainty * factor,
        'uncertainty_type': observation.get('uncertainty_type'),
        'transformation': f'{value} {unit} * {factor} = {normalized} {si_unit}',
        'source_observation_id': observation['id'],
        'calibration_status': 'not_calibrated',
    }


def derive_conductivity(observation):
    n = normalize_property(observation)
    if n['quantity'] != 'electronic_resistivity' or n['value'] <= 0:
        raise ValueError('Conductivity inversion requires positive bulk resistivity, not ASR')
    relation = {'eq': 'eq', 'lt': 'gt', 'le': 'ge', 'gt': 'lt', 'ge': 'le'}[n['relation']]
    return {
        'quantity': 'electronic_conductivity', 'value': 1 / n['value'], 'unit': 'S/m',
        'relation': relation, 'value_role': n['value_role'],
        'source_observation_id': observation['id'],
        'transformation': 'sigma = 1/rho; inverted inequality preserved',
        'conditions': observation['conditions'],
        'calibration_status': 'not_calibrated', 'automatic_solver_binding': False,
    }


def assess_binding(observation, target):
    """A data admission gate, not an operation that edits a scenario or the engine."""
    issues = []
    allowed = {
        'anode_sigma_S_m': 'electronic_resistivity',
        'cathode_sigma_S_m': 'electronic_resistivity',
        'kappa_S_m': 'electrolyte_conductivity',
    }
    if target.get('parameter') not in allowed or allowed.get(target.get('parameter')) != observation.get('quantity'):
        issues.append('no_supported_constitutive_transfer')
    try:
        normalized = normalize_property(observation)
        if normalized['quantity'] == 'electronic_resistivity' and normalized['value'] <= 0:
            issues.append('positive_resistivity_required')
    except (ValueError, KeyError):
        issues.append('normalization_not_admitted')
    if target.get('material_id') != observation.get('material_id'):
        issues.append('material_variant_mismatch')
    if not target.get('explicit_review_id'):
        issues.append('explicit_review_missing')
    if observation.get('relation') != 'eq':
        issues.append('bound_is_not_a_scalar_parameter')
    if observation.get('unit_ambiguity'):
        issues.append('unit_ambiguity')
    source, requested = observation.get('conditions', {}), target.get('conditions', {})
    keys = ['hydration', 'temperature_C', 'pressure_Pa', 'method']
    if observation.get('quantity') == 'electronic_resistivity':
        keys += ['direction', 'contact_contribution']
        if source.get('direction') not in {'in_plane', 'through_plane'}:
            issues.append('direction_geometry_reference_unresolved')
        geometry = target.get('geometry', {})
        if not all(finite(geometry.get(k)) and geometry[k] > 0 for k in ['length_m', 'cross_section_m2']):
            issues.append('electronic_path_geometry_missing')
    else:
        keys += ['electrolyte', 'concentration', 'pH']
    for key in keys:
        a, b = source.get(key), requested.get(key)
        if a is None or a == 'unknown' or b is None or b == 'unknown':
            issues.append(key + '_unresolved')
        elif a != b:
            issues.append(key + '_mismatch')
    return {'eligible_for_binding': not issues, 'reasons': issues,
            'calibration_status': 'not_calibrated', 'automatic_solver_binding': False}


def summarize_offer(offer):
    """Preserve price floors and unknown delivered costs; do not infer cutting yield."""
    size, count = offer.get('sheet_dimensions_cm'), offer.get('pack_count')
    area = None
    if offer.get('dimension_price_binding_verified') and size is not None and count is not None:
        if (len(size) != 2 or not all(finite(x) and x > 0 for x in size)
                or not isinstance(count, int) or isinstance(count, bool) or count <= 0):
            raise ValueError('Invalid sheet dimensions or pack count')
        area = Decimal(str(size[0])) * Decimal(str(size[1])) * count / 10000
    price = offer.get('price_amount')
    if price is not None and (not finite(price) or price < 0):
        raise ValueError('Invalid advertised price')
    if offer.get('price_type') not in {'fixed_variant', 'starting_from', 'request_quote', 'unresolved'}:
        raise ValueError('Unrecognized price type')
    if price is not None and (not isinstance(offer.get('currency'), str) or len(offer['currency']) != 3):
        raise ValueError('Explicit currency is required')
    per_area = None if area is None or price is None else Decimal(str(price)) / area
    floor = offer.get('price_type') == 'starting_from'
    if offer.get('price_type') in {'request_quote', 'unresolved'}:
        per_area = None
    delivered = None
    extras = [offer.get(k) for k in ['shipping_amount', 'tax_amount', 'import_duty_amount']]
    if offer.get('price_type') == 'fixed_variant' and price is not None and all(finite(x) and x >= 0 for x in extras):
        if offer.get('destination_confirmed') and offer.get('all_costs_same_currency'):
            delivered = float(Decimal(str(price)) + sum(Decimal(str(x)) for x in extras))
    return {
        'purchased_sheet_area_m2': None if area is None else float(area),
        'advertised_price_per_purchased_m2': None if per_area is None else float(per_area),
        'price_relation': 'ge' if floor else ('eq' if offer.get('price_type') == 'fixed_variant' else None),
        'currency': offer.get('currency'), 'price_type': offer.get('price_type'),
        'delivered_total': delivered, 'usable_active_area_m2': None,
        'cutting_yield': None, 'mfc_performance_inferred': False,
    }
