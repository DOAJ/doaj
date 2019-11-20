### Upgrade to Python 3
Automated tools run:
	* `2to3 -w . > python3_upgrade_log 2>&1`
	after upgrade, cleanup with:
		+ `find . -name "*.bak" -type f -delete`
		+ `git rm python3_upgrade_log`

### Manual correction process
Below are all of the python files in the project:
```
.
├── deploy
│   ├── doaj_gunicorn_config.py
│   ├── doaj_test_gunicorn_config.py
│   ├── lambda
│   │   └── alert_backups_missing.py
│   └── new_infrastructure_migration_scripts
│       └── copy_data_from_live_to_new.py
├── deploy_old
│   ├── doaj_gunicorn_config.py
│   ├── doaj_test_gunicorn_config.py
│   ├── esbackup.py
│   ├── lambda
│   │   └── alert_backups_missing.py
│   └── mount_s3fs.py
├── doajtest
│   ├── bootstrap.py
│   ├── clonelive.py
│   ├── demo_scripts
│   │   └── async_workflow_notifications_demo.py
│   ├── fixtures
│   │   ├── accounts.py
│   │   ├── applications.py
│   │   ├── article.py
│   │   ├── background.py
│   │   ├── bibjson.py
│   │   ├── common.py
│   │   ├── dois.py
│   │   ├── editors.py
│   │   ├── __init__.py
│   │   ├── issns.py
│   │   ├── journals.py
│   │   ├── provenance.py
│   │   └── snapshots.py
│   ├── functional
│   │   ├── bulk_api.py
│   │   ├── oaipmh_client_test.py
│   │   └── stress_test.py
│   ├── helpers.py
│   ├── __init__.py
│   ├── make_matrix.py
│   ├── mocks
│   │   ├── bll_article.py
│   │   ├── __init__.py
│   │   ├── model_Article.py
│   │   ├── model_Cache.py
│   │   ├── model_Journal.py
│   │   ├── models_Cache.py
│   │   └── store.py
│   └── unit
│       ├── test_anon.py
│       ├── test_api_account.py
│       ├── test_api_bulk_application.py
│       ├── test_api_bulk_article.py
│       ├── test_api_crud_application.py
│       ├── test_api_crud_article.py
│       ├── test_api_crud_journal.py
│       ├── test_api_crud_returnvalues.py
│       ├── test_api_dataobj_cast_functions.py
│       ├── test_api_dataobj.py
│       ├── test_api_discovery.py
│       ├── test_api_errors.py
│       ├── test_article_cleanup_sync.py
│       ├── test_article_match.py
│       ├── test_background.py
│       ├── test_bll_accept_application.py
│       ├── test_bll_article_batch_create_article.py
│       ├── test_bll_article_create_article.py
│       ├── test_bll_article_discover_duplicates.py
│       ├── test_bll_article_get_duplicates.py
│       ├── test_bll_article_is_legitimate_owner.py
│       ├── test_bll_article_issn_ownership_status.py
│       ├── test_bll_authorisations.py
│       ├── test_bll_delete_application.py
│       ├── test_bll_getters.py
│       ├── test_bll_journal_csv.py
│       ├── test_bll_object_conversions.py
│       ├── test_bll_reject_application.py
│       ├── test_bll_update_request.py
│       ├── test_contact.py
│       ├── test_crosswalks_journal2questions.py
│       ├── test_csv_wrapper.py
│       ├── test_datasets.py
│       ├── test_duplicate_report_script.py
│       ├── test_es_snapshots_client.py
│       ├── test_fc_assed_app_review.py
│       ├── test_fc_assed_journal_review.py
│       ├── test_fc_editor_app_review.py
│       ├── test_fc_editor_journal_review.py
│       ├── test_fc_maned_app_review.py
│       ├── test_fc_maned_journal_review.py
│       ├── test_fc_publisher_update_request.py
│       ├── test_fc_readonly_journal.py
│       ├── test_feed.py
│       ├── test_formcontext_emails.py
│       ├── test_formcontext.py
│       ├── test_formrender.py
│       ├── test_forms.py
│       ├── test_index_searchbox.py
│       ├── test_jinja_template_filters.py
│       ├── test_lib_normalise_doi.py
│       ├── test_lib_normalise_url.py
│       ├── test_lock.py
│       ├── test_models.py
│       ├── test_oaipmh.py
│       ├── test_prune_marvel.py
│       ├── test_query_filters.py
│       ├── test_query.py
│       ├── test_regexes.py
│       ├── test_reporting.py
│       ├── test_reserved_usernames.py
│       ├── test_scripts_accounts_with_marketing_consent.py
│       ├── test_sitemap.py
│       ├── test_snapshot.py
│       ├── test_snapshot_tasks.py
│       ├── test_task_article_bulk_delete.py
│       ├── test_task_journal_bulk_delete.py
│       ├── test_task_journal_bulkedit.py
│       ├── test_tasks_ingestarticles.py
│       ├── test_tasks_public_data_dump.py
│       ├── test_task_suggestion_bulkedit.py
│       ├── test_tick.py
│       ├── test_toc.py
│       ├── test_util.py
│       ├── test_withdraw_reinstate.py
│       ├── test_workflow_emails.py
│       └── test_xwalk.py
├── portality
│   ├── api
│   │   ├── __init__.py
│   │   └── v1
│   │       ├── bulk
│   │       │   ├── applications.py
│   │       │   ├── articles.py
│   │       │   └── __init__.py
│   │       ├── common.py
│   │       ├── crud
│   │       │   ├── applications.py
│   │       │   ├── articles.py
│   │       │   ├── common.py
│   │       │   ├── __init__.py
│   │       │   └── journals.py
│   │       ├── data_objects
│   │       │   ├── application.py
│   │       │   ├── article.py
│   │       │   ├── common_journal_application.py
│   │       │   ├── __init__.py
│   │       │   └── journal.py
│   │       ├── discovery.py
│   │       └── __init__.py
│   ├── app_email.py
│   ├── app.py
│   ├── authorise.py
│   ├── background.py
│   ├── bll
│   │   ├── doaj.py
│   │   ├── exceptions.py
│   │   ├── __init__.py
│   │   └── services
│   │       ├── application.py
│   │       ├── article.py
│   │       ├── authorisation.py
│   │       ├── __init__.py
│   │       ├── journal.py
│   │       └── query.py
│   ├── blog.py
│   ├── clcsv.py
│   ├── constants.py
│   ├── core.py
│   ├── crosswalks
│   │   ├── article_doaj_xml.py
│   │   ├── article_form.py
│   │   ├── exceptions.py
│   │   ├── __init__.py
│   │   └── journal_questions.py
│   ├── dao.py
│   ├── datasets.py
│   ├── decorators.py
│   ├── error_handler.py
│   ├── formcontext
│   │   ├── choices.py
│   │   ├── emails.py
│   │   ├── fields.py
│   │   ├── formcontext.py
│   │   ├── formhelper.py
│   │   ├── forms.py
│   │   ├── __init__.py
│   │   ├── render.py
│   │   ├── validate.py
│   │   └── xwalk.py
│   ├── __init__.py
│   ├── lcc.py
│   ├── lib
│   │   ├── analytics.py
│   │   ├── anon.py
│   │   ├── argvalidate.py
│   │   ├── dataobj.py
│   │   ├── dates.py
│   │   ├── es_data_mapping.py
│   │   ├── es_query_http.py
│   │   ├── __init__.py
│   │   ├── isolang.py
│   │   ├── modeldoc.py
│   │   ├── normalise.py
│   │   ├── paths.py
│   │   ├── plugin.py
│   │   ├── query_filters.py
│   │   ├── report_to_csv.py
│   │   └── swagger.py
│   ├── lock.py
│   ├── migrate
│   │   ├── 1089_edit_field_by_query
│   │   │   └── regex_http_to_https.py
│   │   ├── 1196_publisher_struct
│   │   │   ├── __init__.py
│   │   │   └── operations.py
│   │   ├── 1303_nonexistent_editors_assigned
│   │   │   └── nonexistent_editors_assigned.py
│   │   ├── 1390_lcc_regen_subjects
│   │   │   ├── __init__.py
│   │   │   └── operations.py
│   │   ├── 1667_remove_email_from_articles
│   │   │   └── scrub_emails.py
│   │   ├── 20180106_1463_ongoing_updates
│   │   │   ├── __init__.py
│   │   │   ├── operations.py
│   │   │   └── sync_journals_applications.py
│   │   ├── 20180808_1693_article_duplication
│   │   │   └── __init__.py
│   │   ├── 972_appl_form_changes
│   │   │   └── appl_form_changes.py
│   │   ├── autocomplete
│   │   │   └── __init__.py
│   │   ├── continuations
│   │   │   ├── clean_struct.py
│   │   │   ├── extract_continuations.py
│   │   │   ├── __init__.py
│   │   │   ├── mappings.py
│   │   │   ├── restructure_archiving_policy.py
│   │   │   └── test_migration.py
│   │   ├── delete_field_from_type
│   │   │   └── scrub_field.py
│   │   ├── __init__.py
│   │   ├── licenses
│   │   │   ├── missed_journals.py
│   │   │   └── update_licenses.py
│   │   ├── no_editor
│   │   │   └── __init__.py
│   │   ├── p1p2
│   │   │   ├── country_cleanup.py
│   │   │   ├── emails.py
│   │   │   ├── flushuploads.py
│   │   │   ├── journalowners.py
│   │   │   ├── journalrestructure.py
│   │   │   ├── journals_and_suggestions_text_tweaks.py
│   │   │   ├── loadlcc.py
│   │   │   ├── publisheremails.py
│   │   │   ├── remove-0000-issns.py
│   │   │   ├── suggestionrestructure.py
│   │   │   ├── uploadcorrections.py
│   │   │   ├── uploadedfilenames.py
│   │   │   ├── uploadedxml.py
│   │   │   └── userroles.py
│   │   ├── p2oe
│   │   │   ├── apcdata.py
│   │   │   └── uncontinue.py
│   │   ├── st2cl
│   │   │   ├── cluster2.py
│   │   │   ├── cluster.py
│   │   │   ├── emails.py
│   │   │   ├── __init__.py
│   │   │   ├── migrate.py
│   │   │   └── pages.py
│   │   ├── subjects
│   │   │   └── remove_duplicate_subjects.py
│   │   └── tick
│   │       └── check_tick.py
│   ├── models
│   │   ├── account.py
│   │   ├── article.py
│   │   ├── atom.py
│   │   ├── background.py
│   │   ├── bibjson.py
│   │   ├── cache.py
│   │   ├── editors.py
│   │   ├── history.py
│   │   ├── __init__.py
│   │   ├── journal.py
│   │   ├── lcc.py
│   │   ├── lock.py
│   │   ├── oaipmh.py
│   │   ├── openurl.py
│   │   ├── provenance.py
│   │   ├── search.py
│   │   ├── shared_structs.py
│   │   ├── suggestion.py
│   │   └── uploads.py
│   ├── ordereddict.py
│   ├── regex.py
│   ├── scripts
│   │   ├── accounts_with_marketing_consent.py
│   │   ├── accounts_with_missing_api_role.py
│   │   ├── accounts_with_missing_passwords.py
│   │   ├── anon_export.py
│   │   ├── anon_import.py
│   │   ├── applicationrm.py
│   │   ├── article_cleanup_sync.py
│   │   ├── articledump.py
│   │   ├── article_duplicate_analysis.py
│   │   ├── article_duplicate_report.py
│   │   ├── articleload.py
│   │   ├── articlerm.py
│   │   ├── async_workflow_notifications.py
│   │   ├── change_application_status.py
│   │   ├── createuser.py
│   │   ├── generate_iso639b_language_code_schema.py
│   │   ├── history_dirs_reports.py
│   │   ├── history_records_analyse.py
│   │   ├── history_records_assemble.py
│   │   ├── inconsistent_journal_prov_application.py
│   │   ├── __init__.py
│   │   ├── journalcsv.py
│   │   ├── manage_background_jobs.py
│   │   ├── missing_q14q18.py
│   │   ├── missing_quick_reject_emails.py
│   │   ├── news.py
│   │   ├── not_in_doaj_with_articles.py
│   │   ├── orphaned_datasets.py
│   │   ├── prepare_delete_request.py
│   │   ├── prune_es_backups.py
│   │   ├── prune_marvel.py
│   │   ├── public_data_dump.py
│   │   ├── publisher_email_in_doaj.py
│   │   ├── rejected_applications.py
│   │   ├── reports.py
│   │   ├── request_es_backup.py
│   │   ├── sitemap.py
│   │   ├── sync_doaj_records.py
│   │   └── update_mapping_reindex.py
│   ├── settings.py
│   ├── store.py
│   ├── tasks
│   │   ├── article_bulk_delete.py
│   │   ├── article_cleanup_sync.py
│   │   ├── article_duplicate_report.py
│   │   ├── async_workflow_notifications.py
│   │   ├── check_latest_es_backup.py
│   │   ├── consumer_long_running.py
│   │   ├── consumer_main_queue.py
│   │   ├── ingestarticles.py
│   │   ├── __init__.py
│   │   ├── journal_bulk_delete.py
│   │   ├── journal_bulk_edit.py
│   │   ├── journal_csv.py
│   │   ├── journal_in_out_doaj.py
│   │   ├── prune_es_backups.py
│   │   ├── public_data_dump.py
│   │   ├── read_news.py
│   │   ├── redis_huey.py
│   │   ├── reporting.py
│   │   ├── request_es_backup.py
│   │   ├── sitemap.py
│   │   └── suggestion_bulk_edit.py
│   ├── ui
│   │   ├── __init__.py
│   │   └── messages.py
│   ├── upgrade.py
│   ├── util.py
│   └── view
│       ├── account.py
│       ├── admin.py
│       ├── api_v1.py
│       ├── atom.py
│       ├── doaj.py
│       ├── doajservices.py
│       ├── editor.py
│       ├── forms.py
│       ├── __init__.py
│       ├── oaipmh.py
│       ├── openurl.py
│       ├── publisher.py
│       ├── query.py
│       └── status.py
├── scratchpad
│   ├── duplicate_articles
│   │   └── duplicate_articles.py
│   ├── issue171
│   │   └── delete_articles.py
│   ├── issue239
│   │   └── date_histogram.py
│   ├── issue277
│   │   └── dump_articles.py
│   ├── issue290
│   │   └── orphan_issns.py
│   ├── rate_limit
│   │   ├── rate_test2.py
│   │   └── rate_test.py
│   └── sync
│       └── sync_from_remote.py
└── setup.py

54 directories, 345 files
```