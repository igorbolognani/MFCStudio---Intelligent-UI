import { integer, real, sqliteTable, text, uniqueIndex, index } from 'drizzle-orm/sqlite-core';

export const stages = sqliteTable('stages', {
  id:text('id').primaryKey(), ordinal:integer('ordinal').notNull().unique(), name:text('name').notNull(),
});
export const properties = sqliteTable('properties', {
  id:text('id').primaryKey(), stageId:text('stage_id').notNull().references(()=>stages.id),
  name:text('name').notNull(), symbol:text('symbol').notNull(), unit:text('unit').notNull(),
  implementationStatus:text('implementation_status').notNull(), metadata:text('metadata_json').notNull(),
});
export const sources = sqliteTable('sources', {
  id:text('id').primaryKey(), doi:text('doi'), title:text('title').notNull(), url:text('url').notNull(),
  access:text('access').notNull(), scope:text('scope').notNull(), metadata:text('metadata_json').notNull(),
});
export const sourceStages = sqliteTable('source_stages', {
  id:text('id').primaryKey(), sourceId:text('source_id').notNull().references(()=>sources.id),
  stageId:text('stage_id').notNull().references(()=>stages.id), relation:text('relation').notNull(),
});
export const documents = sqliteTable('documents', {
  id:text('id').primaryKey(), sourceId:text('source_id').notNull().references(()=>sources.id),
  title:text('title').notNull(), sha256:text('sha256').notNull(), rawSha256:text('raw_sha256'),
  license:text('license').notNull(), format:text('format').notNull(), objectKey:text('object_key'),
  complete:integer('complete',{mode:'boolean'}).notNull(), textLength:integer('text_length').notNull(),
  metadata:text('metadata_json').notNull(),
});
export const documentChunks = sqliteTable('document_chunks', {
  id:text('id').primaryKey(), documentId:text('document_id').notNull().references(()=>documents.id),
  ordinal:integer('ordinal').notNull(), text:text('text').notNull(), sha256:text('sha256').notNull(),
},t=>[uniqueIndex('document_chunk_ordinal').on(t.documentId,t.ordinal)]);
export const experiments = sqliteTable('experiments', {
  id:text('id').primaryKey(), sourceId:text('source_id').notNull().references(()=>sources.id),
  studyId:text('study_id').notNull(), familyId:text('family_id').notNull(), reactorId:text('reactor_id'),
  replicateId:text('replicate_id'), scope:text('scope').notNull(), conditions:text('conditions_json').notNull(),
});
export const evidenceRecords = sqliteTable('evidence_records', {
  id:text('id').primaryKey(), sourceId:text('source_id').notNull().references(()=>sources.id),
  studyId:text('study_id').notNull(), leakageGroupId:text('leakage_group_id').notNull(),
  scope:text('scope').notNull(), status:text('status').notNull(),
  trainingEligible:integer('training_eligible',{mode:'boolean'}).notNull().default(false),
  data:text('data_json').notNull(),
},t=>[index('evidence_group').on(t.leakageGroupId)]);
export const observations = sqliteTable('observations', {
  id:text('id').primaryKey(), recordId:text('record_id').notNull().references(()=>evidenceRecords.id),
  metric:text('metric').notNull(), value:real('value'), unit:text('unit').notNull(),
  kind:text('kind').notNull(), areaBasis:text('area_basis'), potentialReference:text('potential_reference'),
  locator:text('locator').notNull(), metadata:text('metadata_json').notNull(),
});
export const curves = sqliteTable('curves', {
  id:text('id').primaryKey(), recordId:text('record_id').notNull().references(()=>evidenceRecords.id),
  xMetric:text('x_metric').notNull(), yMetric:text('y_metric').notNull(), xUnit:text('x_unit').notNull(),
  yUnit:text('y_unit').notNull(), extractionMethod:text('extraction_method').notNull(),
  metadata:text('metadata_json').notNull(),
});
export const curvePoints = sqliteTable('curve_points', {
  id:text('id').primaryKey(), curveId:text('curve_id').notNull().references(()=>curves.id),
  ordinal:integer('ordinal').notNull(), x:real('x').notNull(), y:real('y').notNull(), uncertainty:real('uncertainty'),
});
export const scenarios = sqliteTable('scenarios', {
  id:text('id').primaryKey(), userId:text('user_id').notNull(), name:text('name').notNull(),
  currentVersion:integer('current_version').notNull(), updatedAt:text('updated_at').notNull(),
},t=>[index('scenario_owner').on(t.userId)]);
export const scenarioVersions = sqliteTable('scenario_versions', {
  id:text('id').primaryKey(), scenarioId:text('scenario_id').notNull().references(()=>scenarios.id),
  version:integer('version').notNull(), config:text('config_json').notNull(), configSha256:text('config_sha256').notNull(),
  engineVersion:text('engine_version').notNull(), createdAt:text('created_at').notNull(),
},t=>[uniqueIndex('scenario_version').on(t.scenarioId,t.version)]);
export const modelRuns = sqliteTable('model_runs', {
  id:text('id').primaryKey(), userId:text('user_id').notNull(), config:text('config_json').notNull(),
  configSha256:text('config_sha256').notNull(), result:text('result_json').notNull(),
  engineVersion:text('engine_version').notNull(), seedVersion:text('seed_version').notNull(),
  createdAt:text('created_at').notNull(),
});
export const seedVersions = sqliteTable('seed_versions', {
  id:text('id').primaryKey(), contentSha256:text('content_sha256').notNull(), report:text('report_json').notNull(),
  appliedAt:text('applied_at').notNull(),
});
