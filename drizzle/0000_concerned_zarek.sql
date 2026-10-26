CREATE TABLE `curve_points` (
	`id` text PRIMARY KEY NOT NULL,
	`curve_id` text NOT NULL,
	`ordinal` integer NOT NULL,
	`x` real NOT NULL,
	`y` real NOT NULL,
	`uncertainty` real,
	FOREIGN KEY (`curve_id`) REFERENCES `curves`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE TABLE `curves` (
	`id` text PRIMARY KEY NOT NULL,
	`record_id` text NOT NULL,
	`x_metric` text NOT NULL,
	`y_metric` text NOT NULL,
	`x_unit` text NOT NULL,
	`y_unit` text NOT NULL,
	`extraction_method` text NOT NULL,
	`metadata_json` text NOT NULL,
	FOREIGN KEY (`record_id`) REFERENCES `evidence_records`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE TABLE `document_chunks` (
	`id` text PRIMARY KEY NOT NULL,
	`document_id` text NOT NULL,
	`ordinal` integer NOT NULL,
	`text` text NOT NULL,
	`sha256` text NOT NULL,
	FOREIGN KEY (`document_id`) REFERENCES `documents`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE UNIQUE INDEX `document_chunk_ordinal` ON `document_chunks` (`document_id`,`ordinal`);--> statement-breakpoint
CREATE TABLE `documents` (
	`id` text PRIMARY KEY NOT NULL,
	`source_id` text NOT NULL,
	`title` text NOT NULL,
	`sha256` text NOT NULL,
	`raw_sha256` text,
	`license` text NOT NULL,
	`format` text NOT NULL,
	`object_key` text,
	`complete` integer NOT NULL,
	`text_length` integer NOT NULL,
	`metadata_json` text NOT NULL,
	FOREIGN KEY (`source_id`) REFERENCES `sources`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE TABLE `evidence_records` (
	`id` text PRIMARY KEY NOT NULL,
	`source_id` text NOT NULL,
	`study_id` text NOT NULL,
	`leakage_group_id` text NOT NULL,
	`scope` text NOT NULL,
	`status` text NOT NULL,
	`training_eligible` integer DEFAULT false NOT NULL,
	`data_json` text NOT NULL,
	FOREIGN KEY (`source_id`) REFERENCES `sources`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE INDEX `evidence_group` ON `evidence_records` (`leakage_group_id`);--> statement-breakpoint
CREATE TABLE `experiments` (
	`id` text PRIMARY KEY NOT NULL,
	`source_id` text NOT NULL,
	`study_id` text NOT NULL,
	`family_id` text NOT NULL,
	`reactor_id` text,
	`replicate_id` text,
	`scope` text NOT NULL,
	`conditions_json` text NOT NULL,
	FOREIGN KEY (`source_id`) REFERENCES `sources`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE TABLE `model_runs` (
	`id` text PRIMARY KEY NOT NULL,
	`user_id` text NOT NULL,
	`config_json` text NOT NULL,
	`config_sha256` text NOT NULL,
	`result_json` text NOT NULL,
	`engine_version` text NOT NULL,
	`seed_version` text NOT NULL,
	`created_at` text NOT NULL
);
--> statement-breakpoint
CREATE TABLE `observations` (
	`id` text PRIMARY KEY NOT NULL,
	`record_id` text NOT NULL,
	`metric` text NOT NULL,
	`value` real,
	`unit` text NOT NULL,
	`kind` text NOT NULL,
	`area_basis` text,
	`potential_reference` text,
	`locator` text NOT NULL,
	`metadata_json` text NOT NULL,
	FOREIGN KEY (`record_id`) REFERENCES `evidence_records`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE TABLE `properties` (
	`id` text PRIMARY KEY NOT NULL,
	`stage_id` text NOT NULL,
	`name` text NOT NULL,
	`symbol` text NOT NULL,
	`unit` text NOT NULL,
	`implementation_status` text NOT NULL,
	`metadata_json` text NOT NULL,
	FOREIGN KEY (`stage_id`) REFERENCES `stages`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE TABLE `scenario_versions` (
	`id` text PRIMARY KEY NOT NULL,
	`scenario_id` text NOT NULL,
	`version` integer NOT NULL,
	`config_json` text NOT NULL,
	`config_sha256` text NOT NULL,
	`engine_version` text NOT NULL,
	`created_at` text NOT NULL,
	FOREIGN KEY (`scenario_id`) REFERENCES `scenarios`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE UNIQUE INDEX `scenario_version` ON `scenario_versions` (`scenario_id`,`version`);--> statement-breakpoint
CREATE TABLE `scenarios` (
	`id` text PRIMARY KEY NOT NULL,
	`user_id` text NOT NULL,
	`name` text NOT NULL,
	`current_version` integer NOT NULL,
	`updated_at` text NOT NULL
);
--> statement-breakpoint
CREATE INDEX `scenario_owner` ON `scenarios` (`user_id`);--> statement-breakpoint
CREATE TABLE `seed_versions` (
	`id` text PRIMARY KEY NOT NULL,
	`content_sha256` text NOT NULL,
	`report_json` text NOT NULL,
	`applied_at` text NOT NULL
);
--> statement-breakpoint
CREATE TABLE `source_stages` (
	`id` text PRIMARY KEY NOT NULL,
	`source_id` text NOT NULL,
	`stage_id` text NOT NULL,
	`relation` text NOT NULL,
	FOREIGN KEY (`source_id`) REFERENCES `sources`(`id`) ON UPDATE no action ON DELETE no action,
	FOREIGN KEY (`stage_id`) REFERENCES `stages`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE TABLE `sources` (
	`id` text PRIMARY KEY NOT NULL,
	`doi` text,
	`title` text NOT NULL,
	`url` text NOT NULL,
	`access` text NOT NULL,
	`scope` text NOT NULL,
	`metadata_json` text NOT NULL
);
--> statement-breakpoint
CREATE TABLE `stages` (
	`id` text PRIMARY KEY NOT NULL,
	`ordinal` integer NOT NULL,
	`name` text NOT NULL
);
--> statement-breakpoint
CREATE UNIQUE INDEX `stages_ordinal_unique` ON `stages` (`ordinal`);