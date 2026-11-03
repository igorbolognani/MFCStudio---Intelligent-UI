"""Audit reference-arm curation without promoting it into the predictive corpus.

Run with --documents DIR to verify the privately preserved source bytes too.
JSON paths and document locators preserve the manual extraction lineage.
"""
from pathlib import Path
import argparse
from collections import Counter
import gzip
import hashlib
import json
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'science'))
from material_data import normalize_property

FOLDER = ROOT / 'research/reference-families-v0.1'


def verify_bytes(path, document):
    raw = path.read_bytes()
    if path.suffix == '.gz':
        raw = gzip.decompress(raw)
    if len(raw) != document['bytes'] or hashlib.sha256(raw).hexdigest() != document['sha256']:
        raise ValueError('Document version/hash mismatch: ' + document['id'])
    return raw


def compare_known(a, b):
    """Unknown or missing fields never establish equality between configurations."""
    different, unresolved = [], []
    unknown = (None, 'not_reported', 'unknown', '')
    def visit(x, y, key):
        if x in unknown or y in unknown:
            unresolved.append(key)
        elif isinstance(x, dict) and isinstance(y, dict):
            keys = set(x) | set(y)
            if not keys:
                unresolved.append(key)
            for child in sorted(keys):
                visit(x.get(child), y.get(child), key + '.' + child)
        elif isinstance(x, list) and isinstance(y, list):
            if not x and not y:
                unresolved.append(key)
            for i in range(max(len(x), len(y))):
                visit(x[i] if i < len(x) else None, y[i] if i < len(y) else None, key + '[' + str(i) + ']')
        elif x != y:
            different.append(key)
    for key in sorted(set(a) | set(b)):
        visit(a.get(key), b.get(key), key)
    return {'same_configuration_demonstrated': not different and not unresolved and bool(a),
            'known_differences': different, 'unresolved': unresolved}


def build(data=None, documents_dir=None):
    d = data or json.loads((FOLDER / 'catalog.json').read_text())
    stage_ids = [s['id'] for s in d['stages']]
    canonical = json.loads((ROOT / 'research/materials-v0.1/catalog.json').read_text())
    if stage_ids != [s['stage_id'] for s in canonical['stage_acquisition_plan']]:
        raise ValueError('Canonical eleven-stage order changed')
    sources = {s['id']: s for s in d['sources']}
    if len(sources) != len(d['sources']) or len({s['doi'].lower() for s in sources.values()}) != len(sources):
        raise ValueError('Duplicate source identifier or DOI')
    docs = {s['id']: s for s in d['documents']}
    if len({r['id'] for r in d['reported_reference_results']}) != len(d['reported_reference_results']):
        raise ValueError('Duplicate reference result')
    arms = {a['id']: a for a in d['reference_arms']}
    if len(arms) != len(d['reference_arms']):
        raise ValueError('Duplicate reference arm')
    facts = []
    for arm in arms.values():
        if (not sources[arm['source_id']]['full_text_acquired'] or not arm['reference_role_verified']
                or arm['training_eligible'] or not arm['gaps']):
            raise ValueError('Reference admission or limitations lost')
        if [s['id'] for s in arm['stages']] != stage_ids:
            raise ValueError('Incomplete stage inventory')
        if arm['document_sha256'] != docs[arm['document_id']]['sha256']:
            raise ValueError('Configuration belongs to a different source version')
        for i, stage in enumerate(arm['stages']):
            if not stage['locator'] or stage['status'] not in {'reported', 'shared', 'not_applicable', 'not_reported', 'not_measured'}:
                raise ValueError('Missing provenance or invalid missing-data status')
            for key, value in stage['facts'].items():
                facts.append({'id': arm['id'] + ':' + stage['id'] + ':' + key,
                              'source_id': arm['source_id'], 'document_id': arm['document_id'],
                              'document_sha256': arm['document_sha256'], 'stage_id': stage['id'],
                              'locator': stage['locator'], 'catalog_json_pointer':
                              '/reference_arms/' + str(list(arms).index(arm['id'])) + '/stages/' + str(i) + '/facts/' + key,
                              'value': value, 'extraction': 'contextually_reviewed_manual_reference_methods',
                              'training_eligible': False})
    xml_doc = docs['RF02-main']
    root = ET.fromstring(verify_bytes(ROOT / xml_doc['repository_path'], xml_doc))
    normalized_results = []
    conversions = {'uW/cm2': (.01, 'W/m2'), 'mW/m2': (.001, 'W/m2'), 'W/m2': (1, 'W/m2'), '%': (.01, '1')}
    for result in d['reported_reference_results']:
        if result['arm_id'] not in arms or result['training_eligible'] or not result['locator']:
            raise ValueError('Result lacks reference-arm provenance')
        if result['document_sha256'] != docs[result['document_id']]['sha256']:
            raise ValueError('Result belongs to a different source version')
        if result['source_id'] == 'RF02':
            if result['lab'] not in {'UNM', 'TUB', 'UFZ'} or result['cycle'] not in {5, 6}:
                raise ValueError('Unreviewed lab or post-reseeding phase cannot enter reference extraction')
            table_id = 'cssc202100294-tbl-000' + ('2' if result['cycle'] == 5 else '3')
            table = next(t for t in root.findall('.//table-wrap') if t.get('id') == table_id)
            row = next([''.join(c.itertext()).strip() for c in tr] for tr in table.findall('.//tr')
                       if ''.join(tr[0].itertext()).strip() == result['lab'])
            value, plus_minus = map(float, row[3].split('±'))
            if value != result['value'] or plus_minus != result['plus_minus']:
                raise ValueError('Transcription differs from original JATS table')
        factor, unit = conversions[result['unit']]
        normalized_results.append({**result, 'normalized': {
            'value': result['value'] * factor, 'unit': unit,
            'plus_minus': result.get('plus_minus') * factor if result.get('plus_minus') is not None else None,
            'uncertainty_type': result['uncertainty_type'],
            'transformation': f'original value and reported dispersion multiplied by {factor}',
            'area_basis': result['area_basis'], 'absolute_power_inferred': False}})
    normalized_specs = [{**s, 'normalized': normalize_property(s)} for s in d['commercial_specs']]
    verification = []
    for doc in d['documents'] + d['commercial_documents']:
        local = ROOT / doc['repository_path'] if doc.get('repository_path') else (
            Path(documents_dir) / doc['local_acquisition_path'].removeprefix('documents/') if documents_dir else None)
        if local:
            verify_bytes(local, doc)
        verification.append({'id': doc['id'], 'bytes_verified': bool(local)})
    coverage = [{'stage_id': stage, 'configurations_with_stage': sum(any(s['id'] == stage for s in a['stages']) for a in arms.values()),
                 'statuses': dict(Counter(s['status'] for a in arms.values() for s in a['stages'] if s['id'] == stage))}
                for stage in stage_ids]
    return {'version': d['version'], 'report': {
        'screened_primary_sources': len(sources), 'full_main_article_texts_acquired': sum(s['full_text_acquired'] for s in sources.values()),
        'main_articles_with_figures_acquired': sum(s['full_document_acquired'] for s in sources.values()),
        'article_formats': {'PDF': 9, 'JATS_XML': 4},
        'main_article_figure_assets_pending': [s['id'] for s in sources.values() if s['full_text_acquired'] and not s['article_figures_acquired']],
        'full_main_article_texts_pending': [s['id'] for s in sources.values() if not s['full_text_acquired']],
        'supplements_acquired': sum(t['type'] == 'supplement' for t in d['documents']),
        'commercial_documents': len(d['commercial_documents']), 'reference_configurations': len(arms),
        'reference_configuration_facts': len(facts), 'reported_reference_results': len(normalized_results),
        'normalized_commercial_specs': len(normalized_specs), 'coverage': coverage,
        'substrates_in_six_curated_configurations': dict(Counter(a['substrate'] for a in arms.values())),
        'cross_paper_identical_configurations_demonstrated': 0,
        'training_eligible': 0, 'curves_digitized_this_round': 0, 'new_prices': 0,
        'production_seed_updated': False,
        'frequency_scope': 'purposeful acquisition cohort, not global literature prevalence'},
        'configuration_fact_ids': [f['id'] for f in facts], 'reference_results': normalized_results,
        'commercial_specs': normalized_specs, 'document_verification': verification}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--documents', help='Private source-document directory, for full-byte verification')
    parser.add_argument('--output', help='Optional complete audit output (default: tracked processed.json)')
    args = parser.parse_args()
    data = build(documents_dir=args.documents)
    output = Path(args.output) if args.output else FOLDER / 'processed.json'
    output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(data['report'], ensure_ascii=False, indent=2))
