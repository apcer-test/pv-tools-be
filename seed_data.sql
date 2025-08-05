-- This script seeds the database with the necessary data for the AI extraction module
-- including LLM providers, models, credentials, prompt templates, and extraction agents.

-- 1. Insert LLM Providers
INSERT INTO llm_provider (id, name, base_url, is_active, created_at, updated_at) 
VALUES 
('01K1AH795C22GQEQJDZ9TZY726', 'openai', NULL, true, NOW(), NOW()),
('01K1AKPA50XK62P142N2DXNRWV', 'gemini', NULL, true, NOW(), NOW())
ON CONFLICT (id) DO NOTHING;

-- 2. Insert LLM Models
INSERT INTO llm_model (id, provider_id, name, context_tokens, input_price_1k, output_price_1k, launch_date, is_deprecated, created_at, updated_at) 
VALUES 
('01K1AJQMT166T9HN8TYYCAK6S6', '01K1AH795C22GQEQJDZ9TZY726', 'gpt-4.1-mini', 500, 0.0004, 0.0016, NULL, false, NOW(), NOW()),
('01K1AKQC53TNBEJZ96DJQW577F', '01K1AKPA50XK62P142N2DXNRWV', 'gemini-2.5-flash', 500, 0.0004, 0.0016, NULL, false, NOW(), NOW())
ON CONFLICT (id) DO NOTHING;

-- 3. Insert LLM Credentials
INSERT INTO llm_credential (id, provider_id, alias, api_key_enc, rate_limit_rpm, is_active, created_at, updated_at) 
VALUES 
('01K1AKWR7BEKTYYF0DJHD24G8Z', '01K1AH795C22GQEQJDZ9TZY726', 'gpt_api_key', 'variable', NULL, true, NOW(), NOW()),
('01K1AMBVAEKCBR17J58HXSSMJX', '01K1AKPA50XK62P142N2DXNRWV', 'gemini_api_key', 'variable', NULL, true, NOW(), NOW())
ON CONFLICT (id) DO NOTHING;

-- 4. Insert Fallback Chain
INSERT INTO fallback_chain (id, name, max_total_retries, is_active, created_at, updated_at) 
VALUES 
('01K1AGGAEZAGKMS9YMZYM1YYWT', 'Default AI Extraction Chain', 3, true, NOW(), NOW())
ON CONFLICT (id) DO NOTHING;

-- 5. Insert Fallback Steps
INSERT INTO fallback_step (id, chain_id, seq_no, model_id, llm_credential_id, max_retries, retry_delay_ms, temperature_override, max_tokens_override, stop_sequences, created_at, updated_at) 
VALUES 
('01K1ANQN0Q429AMV41FQ8Y8ANR', '01K1AGGAEZAGKMS9YMZYM1YYWT', 1, '01K1AJQMT166T9HN8TYYCAK6S6', '01K1AKWR7BEKTYYF0DJHD24G8Z', 3, 500, 0.00, 1024, NULL, NOW(), NOW()),
('01K1ANRN0PM6972XF7WJD5G17W', '01K1AGGAEZAGKMS9YMZYM1YYWT', 2, '01K1AKQC53TNBEJZ96DJQW577F', '01K1AMBVAEKCBR17J58HXSSMJX', 3, 500, 0.00, 1024, NULL, NOW(), NOW())
ON CONFLICT (id) DO NOTHING;

-- 6. Insert Prompt Templates
INSERT INTO prompt_template (id, doc_type_id, version, language, temperature, top_p, max_tokens, template_body, created_at, updated_at) 
VALUES 
('01K1AN2VDDW1KB5MW0CQG86HG9', '01K1AGGAEZAC16072DAMTBSXF2', 1, 'en', 0.20, 1.00, 8000, '# Medical CIOMS Form Data Extraction Prompt

You are an expert medical document analyst specializing in extracting structured data from CIOMS forms and medical safety reports. Extract ONLY the following specific data points from the provided PDF images, organizing them according to these exact section labels and field names.

## Instructions

> 1. Extract **ONLY** the data fields specified below in the Data Extraction Template.
> 2. Present data in a **structured JSON format** with **nested objects** for each section.
> 3. If a field is **not found** or **empty** in the PDF, include the field with a `null` value.
> 4. **Do not include** any fields that are not explicitly listed below.
> 5. Return only dictionary JSON and not list JSON.
> 6. All the fields which have list of values should be extracted as list.
> 7. Always remember, in check box fields, checkboxes are on the left side of the field names.
> 8. NOTE: There is a pattern to find disease term, LLT and PT which is : 1) disease_term (LLT (LLT_code), PT (PT_code)) or disease_term [LLT]
> 9. Off Label Dosing is considered as adverse event.
> 10. All the fields which are assigned the data type "string" must be extracted as string.
> 11. **Improtant** : All the date fields should be in the format `DD-MM-YYYY` or `MM-YYYY` or `YYYY`.

## Expexted Output Format (dictionary JSON)

```json
{
    "patient_information": {
        "patient": {
            "patient_id": <extract just patient initials from the "1. Patient Initials" section> or null,
            "dob": <extract date of birth from the "2. Date of Birth" section> or null,
            "age" : <extract patient age in number from the "2a. Age" or "DESCRIBE REACTION" continuation section> or null,
            "age_unit": <extract patient age unit from the "2a. Age" or "DESCRIBE REACTION" continuation section (e.g. "Days", "Months", "Years")> or null,
            "gender": <extract patient gender from the "3. Sex" or "DESCRIBE REACTION" continuation section> or null,
            "pregnancy": <extract true if its mentioned that patient is pregnent else false>
            "weight": <extract patient weight with unit from the "3a. Weight" or "DESCRIBE REACTION" continuation section> or null,
            "height": <extract patient height with unit from the "3b. Height" or "DESCRIBE REACTION" continuation section> or null,
            "ethnic_origin": <extract patient ethnic origin from the "DESCRIBE REACTION" continuation section> or null,
            "record_no": <extract the exactly Subject Id from the "MANUFACTURER INFORMATION" section (e.g. Subject Id: abc, then extract abc else null)> or null
        },
        "medical_history": <(Extraction must be from pdf from the "23. OTHER RELEVANT HISTORY" and "23. OTHER RELEVANT HISTORY" continuation section)> [
        # This should only have Current Condition, Allergies, Allergies to medication, Procedure and Historical Condition. IMPORTANT: DO NOT INCLUDE HISTORICAL DRUG
            {
                
                "disease_term": <extract disease term> or null,
                "LLT": <extract LLT name(not LLT numeric code) for the disease term> or null,
                "start_date": <extract start date of the disease term> or null,
                "end_date": <extract end date of the disease term> or null,
                "continuing": <YES if the disease is continuing (YES/NO)> or null,
                "famiy_history": <extract family history> or null,
                "disease_comment": <extract if the disease comment is provided else null> or null
                "cause_of_death": <extract family history> or null,
                "performed_autopsy": <true if preformered autopsy else false>,
                "date_of_autopsy": <extract date of autopsy> or null,
                "date_of_death": <extract date of death if patient died> or null
            }
        ],
        "parent": {
            "gender": <extract gender of the parent from the "23. OTHER RELEVANT HISTORY" or ADDITIONAL INFORMATION section> or null,
            "age": <extract age of the parent from the "23. OTHER RELEVANT HISTORY" or ADDITIONAL INFORMATION section> or null,
            "age_unit": <extract age unit of the parent from the "23. OTHER RELEVANT HISTORY" or ADDITIONAL INFORMATION section> or null,
            "lmp_date": <extract mothers Last Menstrual Period(LMP) date from "DESCRIBE REACTION" continuation section> or null,
            "pre_existing_medical_condition": <extract pre-existing medical condition of parent from "DESCRIBE REACTION" continuation section> or null
        }
    }
}', NOW(), NOW()),

('01K1AN2VDD9N08DFVKG0HZ3K81', '01K1AGGAEZAC16072DAMTBSXF2', 1, 'en', 0.20, 1.00, 8000, '1. Extract **ONLY** the data fields specified below in the Data Extraction Template.
> 3. Present data in a **structured JSON format** with **nested objects** for each section.
> 4. If a field is **not found** or **empty** in the PDF, include the field with a `null` value.
> 5. **Do not include** any fields that are not explicitly listed below.
> 7. IMPORTANT: All the dates in string fields should be extracted in the format `DD-MM-YYYY` or `MM-YYYY` or `YYYY`.
> 8. Return only dictionary JSON and not list JSON.
> 9. All the fields which have list of values should be extracted as list.
> 10. Always remember, in check box fields, checkboxes are on the left side of the field names. Crossed, Checked and Filled, all are considered as checked
> 11. NOTE: There is a pattern to find disease term, LLT and PT which is : 1) disease_term (LLT (LLT_code), PT (PT_code)) or disease_term [LLT]
> 12. Off Label Dosing is considered as adverse event.
> 13. All the fields which are assigned the data type "string" must be extracted as string.
> 14. IMPORTANT: A checkbox is considered "checked" if it contains a checkmark (✓), a cross (X), is ticked, or is filled in.
```json
{
    "adverse_event": <extract list of adverse events from the "DESCRIBE REACTION" or "DESCRIBE REACTION" continuation section> [
        {   
            "reported_term": <extract just the reported term> or null,
            "LLT": <extract LLT name(not LLT numeric code)> or null,
            "outcome": <extract outcome of the adverse event> or null,
            "onset_date": <extract start date of the adverse event> or null,
            "cessation_date": <extract end date of the adverse event> or null,
            "death" (bool): <extract true if death of the "PATIENT DIED" cehckbox is checked/crossed in the "8-12 CHECK ALL APPROPRIATE TO ADVERSE REACTION" section> or false,
            "caused_prolongated_hospitalization" (bool): <extract this from "8-12 CHECK ALL APPROPRIATE TO ADVERSE REACTION" section> or false,
            "hospitalisation_start_date": <extract the start date of hospitalisation from "DESCRIBE REACTION" continuation> or null,
            "hospitalisation_end_date": <extract the end date of hospitalisation from "DESCRIBE REACTION" continuation> or null,
            "hospitalisation_duration": <exrtact the hospitalisation duration from "DESCRIBE REACTION" continuation> or null,
            "other_serious_medical_event" (bool): <extract this from "8-12 CHECK ALL APPROPRIATE TO ADVERSE REACTION" section> or false
        }
    ]
}', NOW(), NOW()),

('01K1AN2VDDTSP43PEGNT6B1BE4', '01K1AGGAEZAC16072DAMTBSXF2', 1, 'en', 0.20, 1.00, 8000, '# Medical CIOMS Form Data Extraction Prompt - **PRODUCT SECTION** (REV 2)

        You are an expert medical document analyst specialising in extracting structured data from CIOMS forms and medical safety reports.
        Extract **ONLY** the data points described below, following every rule precisely.

        ---------------------------------------------------------------------
        GENERAL INSTRUCTIONS
        ---------------------------------------------------------------------
        1. Extract **only** the fields listed in the template - no extras.
        2. Output must be **valid JSON (dictionary)** - **no markdown wrappers**.
        3. If a field is missing/blank, use `null`.
        4. **Improtant** : All the date fields should be in the format `DD-MM-YYYY` or `MM-YYYY` or `YYYY`.
        5. In check-box questions, remember: the check box is on the **left** side of the label.
        6. A drug is **HISTORICAL** if it appears in section 23 (or its continuation).
        7. Do **NOT** deduplicate drugs. If the same drug appears twice (e.g., two regimens), create **two separate objects**.
        8. **Improtant** : When you are extracting the dosage frequency, it will be given in the format "2 in 1 Day" means frequency is 1 and frequency time uint is Day and 2 is the number of units.

        ---------------------------------------------------------------------
        DATA MODEL (IMPORTANT!)
        ---------------------------------------------------------------------
        • `product_information` is a **LIST**.
        • **Each element** of that list is **one drug/product** (SUSPECT, CONCOMITANT or HISTORICAL).
        
        ---------------------------------------------------------------------
        SECTION-TO-FIELD MAPPING
        ---------------------------------------------------------------------
        • Sections 14. SUSPECT DRUG / 15. DAILY DOSE / 22. CONCOMITANT DRUG (+ their continuations) → core product & dosage data.
        • Section 17 → indication data.
        • Sections 7 + 13 narrative → additional dosage details when present.
        • Section 23 → identify **HISTORICAL** drugs.

        ---------------------------------------------------------------------
        REMINDERS
        ---------------------------------------------------------------------
        • Keep the JSON **flat** at root except for `product_information` list and its nested objects.
        • No other top-level keys unless explicitly specified elsewhere in the code.
        • Validate the final JSON before returning.
        
        ---------------------------------------------------------------------
        EXPECTED OUTPUT SKELETON
        ---------------------------------------------------------------------
        ```json
        {
        "product_information": [
            {
            "product_flag": <Extract from section 14, 15, 22 and their continuation identifying SUSPECT / CONCOMITANT / HISTORICAL. This is a single value field indicating the role of the product in the adverse event. Flag can be: Suspect, Concomitant, Interacting. Example: "SUSPECT", "CONCOMITANT", "INTERACTING"> or null,
            "product_name_as_reported": <Extract only the product name or description (e.g., "OXCARBAM") from section 14, 15, 22 and their continuation. Do NOT extract form of admin, route, or other attributes. For multiple values, there may be a "Continue" indication in the structure part, and complete information will be in leading pages. Do not duplicate product names, as continuation sections may repeat names. If not found, return null. Example: "OXCARBAM", "PERINDOPRIL",
            "indication": [
                {
                    "indication_term": <Extract indication term from section 14, 15, 22 and their continuation, one per drug. This is the information available with drug name. If not available, extract from narrative. For Suspect drugs, it will be in structure; for Concomitant, it may be in narrative. Example: "Prostate cancer", "Conc drug A for fever", "Conc drug A and B for fever", "Conc drug A for Fever conc drug B for cold"> or null,
                    "llt": <Extract LLT (Lowest Level Term, the most specific MedDRA term describing the indication) from section 17, one per drug. This will be from MedDRA. Example: "Prostate cancer", "Diabetes", "Arterial hypertension"> or null,
                }
                // -> Additional indication objects for the product follow …
            ],
            "dosage": [ 
                {
                    "frequency": <extract dosing frequency from sections "15. DAILY DOSE(S)" section or narrative> or null,
                    "number_of_units": <extract number of separate dosage units taken at a particular time or within a given time interval> or null,
                    "frequency_time": <extract frequency time text, if any> or null,
                    "therapy_start_date": <Extract therapy start date(s) from sections 14/18/22 or narrative. This is the date on which therapy started. This will be available in structured form. Example: "01-01-2024", "Asked but Unknown"> or null,
                    "therapy_start_date_text": <Extract the original text for therapy start date, if available. This is date information that might be available in text form, like "therapy started 15 days ago". If not found, return null> or null,
                    "therapy_end_date": <Extract therapy end date(s) from sections 14/18/22 or narrative. This is the date on which therapy ended. This will be available in structured form. Example: "27-01-2025", "03-03-2025"> or null,
                    "therapy_end_date_text": <Extract the original text for therapy end date, if available. This is date information that might be available in text form, like "therapy ended 2 days ago". If not found, return null> or null,
                    "duration": <extract the duration of time in which the drug has been taken. This is the time period between therapy start date and therapy end date, or as explicitly stated in the document. If not found, return null.>,
                    "duration_unit": <extract the unit of time for the duration, e.g., "Days", "Weeks", "Months", or null>,
                    "dose": <extract dose amount(s) from sections 14/15/22 or narrative. Amount of drug that patient has taken. Example: 12.5, 10> or null,
                    "dose_unit": <extract dose unit(s) from sections 14/15/22 or narrative. This is the unit of the drug like mg, ml. Example: milligram(s), mg, ml> or null,
                    "daily_dose": <extract total amount of drug taken in a day. Example: If 50mg twice a day, then daily dose is 100mg> or null,
                    "dosage_text": <extract free-text dosage info, if available. We can get the dosage information in free text like "XYX drug started 2 months ago" or "Patient was prescribed 50 mg once daily"> or null,
                }
                // -> Additional dosage objects for the product ollow …
            ],
            "lot_no_information": [
                {
                    "batch_lot_no": <extract batch/lot number from sections 14/15/22. This may or may not be available. We can get value like Unknown or 123 etc> or null,
                    "expiry_date_text": <extract the drug lot expiry date from narrative. This is the drug lot expiry which will be there in narrative.> or null
                }
                // -> Additional dosage objects for the product follow …
            ],
            "parent_route_of_admin_details": [
                {
                    "parent_route_of_admin_text": <extract the free-text description of the route of administration. This is a free-text description of the route of admin. Valid for parent-child case> or null
                }
                // -> Additional parent_route_of_admin_details objects for the product follow …
            ],
            "pharmaceutical_dose_form": [
                {
                    "pharmaceutical_dose_form_admin_text": <extract the free-text description of the dosage form. This field is for a free-text description of the dosage form. Example: "Powder and solvent for suspension for injection", "The patient was prescribed an effervescent tablet for her headache."> or null
                }
                // -> Additional pharmaceutical_dose_form objects for the product follow …
            ],
            "additional_information": {
                    "expiration_date": <extract the expiry date mentioned on the drug. This may or may not be available. Example: 12-2025, 01-01-2024> or null,
                },
                "app_no_lot_no": [
                    {
                        "lot_no": {
                            "batch_lot_no": <extract batch or lot number (the unique number of drug stripe or lot) from sections 14/15/22 or additional information. This may or may not be available. Example: "12345", "Unknown", "A1B2C3"> or null,
                        }
                    }
                    // -> Additional app_no_lot_no objects for the product follow …
                ]
                },
                "substance_info": [
                    {
                        "substance_name": <Extract substance name(s) from sections 14/18/22 and continuations titled with "Active Substance". This is the active ingredient or substance within the product. This can be available in structured value under "Active Substance" label or as free text. Example: "OXCARBAZEPINE", "TAMSULOSIN", "TROSPIUM CHLORIDE", "METFORMIN HYDROCHLORIDE and SITAGLIPTIN PHOSPHATE", "PERINDOPRIL", "DAPAGLIFLOZIN PROPANEDIOL MONOHYDRATE"> or null,
                        "strength": <Extract strength value(s) for the drug. This is the numeric value found under the "Form strength" label. Example: 0.4, 20, 10> or null,
                        "strength_unit": <Extract strength unit(s) for the drug. This is the unit of the strength value, e.g., mg in 20mg. Example: "Milligram", "mg"> or null,
                    }
                    // -> Additional substance_info objects for the product follow …
                ],
                "expectedness": [
                    {
                        "reported_term": <Extract the main event/adverse event/reported term(s) from the labeling section as string. This is free text information available indicating the event that happened. Example: "Rash on the right thigh developing into a squamous erythroderma across the whole body">,
                    }
                    // -> Additional expectedness objects for the product follow …
                ],
                "analysis": [
                    {
                        "action_taken_with_drug": <Extract the action taken with the drug. Find in the causality section or the 7+13. DESCRIBE REACTION(S) section and its continuations.>,
                        "causality_information": {
                            "reported_term": <Extract the reported term for causality assessment. This is free text information available indicating the event that happened. Example: "Rash on the right thigh developing into a squamous erythroderma across the whole body">,
                            "reported_causality": <Extract the information provided by the reporter for the adverse event. This is available with the field: Causality as per reporter. Example: "Reasonable possibility"> or null,
                            "DeChallenge": <Extract information about dechallenge (whether the drug was discontinued or dose reduced after an AE occurred, and the outcome). Dechallenge refers to the discontinuation or reduction of the dose of the suspect drug after an AE has occurred. Positive dechallenge: The AE subsides or disappears after the drug is stopped or the dose is reduced. This supports a causal link. Negative dechallenge: The AE does not subside or continues even after the drug is stopped or the dose is reduced. This makes a causal link less likely. Value will be: YES, NO, NA> or null,
                            "ReChallenge": <Extract information about rechallenge (whether the drug was re-administered and the outcome). Rechallenge refers to the re-administration of the suspect drug after it has been discontinued. Positive rechallenge: The AE reappears upon re-administering the drug. This provides strong support for a causal relationship. Negative rechallenge: The AE does not reappear upon re-administering the drug. This argues against a causal relationship. Value will be: YES, NO, NA> or null,
                        }
                    }
                    // ⇢ Additional analysis objects follow …
                ]
            }
            // ⇢ Additional product objects follow …
          ]
        ```
        ---
        """', NOW(), NOW()),

('01K1AN2VDDQ3GFE224G1VSB9DW', '01K1AGGAEZAC16072DAMTBSXF2', 1, 'en', 0.20, 1.00, 8000, '# Medical CIOMS Form Data Extraction Prompt

You are an expert medical document analyst specializing in extracting structured data from CIOMS forms and medical safety reports. Extract ONLY the following specific data points from the provided PDF images, organizing them according to these exact section labels and field names.

## Instructions

> 1. Extract **ONLY** the data fields specified below in the Data Extraction Template.
> 2. Present data in a **structured JSON format** with **nested objects** for each section.
> 3. If a field is **not found** or **empty** in the PDF, include the field with a `null` value.
> 4. **Do not include** any fields that are not explicitly listed below.
> 5. **Improtant** : All the date fields should be in the format `DD-MM-YYYY` or `MM-YYYY` or `YYYY`.
> 6. Return only dictionary JSON and not list JSON.
> 7. All the fields which have list of values should be extracted as list.

## Expexted Output Format (dictionary JSON)

```json
{
    "case_details": {
            "latest_received_date": <Extract date from 24c. DATE RECEIVED BY MANUFACTURER section> or null,
            "primary_source_country": <Extract country of patient from "1a. COUNTRY"  or "1a. COUNTRY" Continuation> or null,
            "medicaly_confirmed": <true if HEALTHCARE PROFESSIONAL box is checked/Crossed in the 24d. REPORT SOURCE section else false"> or false,
            "link": {
                "link_report_no": <Any ID. mentioned in  DESCRIBE REACTION Continuation for linked case, if multiple represented as comma seperated string> or null,
                "reason_for_linking": <Why this case is linked to another case> or null
            },
            "case_numbers": {
                "authority_no": <reference number of the authority, should be extracted from the "DESCRIBE REACTION" continuation section> or null,
                "local_reference_no": <extracted from the "MFR CONTROL NO." section> or null
                "other_refernece_number": <reference numbers mentioned in "DESCRIBE REACTION" continuation should be extracted here, there can be multiple reference numbers represented in comma seperated string> or null
            },
            "report_source": {
                "type_of_report" Literal["STUDY" | "SPONTANOUS"]: <In "24d. REPORT SOURCE" sectionif STUDY is checked/Crossed (X) then it is "STUDY" else it is "SPONTANOUS"> or null,
                "report_source" Literal["LITERATURE" | null]: < ONLY CHECK THE CHECKBOX OF THE LITERATURE, IGNORE ALL OTHERS In "24d. REPORT SOURCE" section if LITERATURE is checked/Crossed then it is "LITERATURE" and if check box is empty it is null> or null,
            }
    },
    "reporter_information": <extract list of proper reporter information from the "DESCRIBE REACTION" or "DESCRIBE REACTION" continuation section>[
        {
            "primary_source_for_regulatory_submission": <true if its first reporter mentioend in the file else false>,
            "title": <title of the reporter> or null,
            "first_name": <first name of the reporter> or null,
            "middle_name": <middle name of the reporter> or null
            "last_name": <last name of the reporter> or null,
            "health_care_professional": <true if HEALTHCARE PROFESSIONAL box is checked/Crossed in the image provided in request> or null,
            "reporter_type" Literal["Physician" | "Pharmacist" | "Lawyer" | "Consumer" | "Other health care professional" | "Other non health care professional"]: <extract reporter type>,
        }
    ],
    "literature": <extract list of literature details from the "DESCRIBE REACTION" continuation section>[
        # In the citation the publication date, edition and page number are mentioned in the given format -> (publication_date.edition.page_numbers)
        # Seperator between publication date, edition and page number might vary so extract those details smartly
        # Example In (2024.10.13,14,15) publication_date = 2024, edition=10, page_numbers = 13-15
        {
            "article_title": <MUST extract full article title> or null,
            "journal_title": <MUST extract full journal title> or null,
            "publication_date": <extract publication date of the article> or null,
            "edition": <extract edition of the journal> or null,
            "literature_reference": <Citation which have author names, literature title, journal title, publication date, edition, page number> or null,
            "page_numbers": <extract page number of the article> or null,
            "doi_name" <extract doi url of the article> or null,
            "authors": <extract list of authors from the "DESCRIBE REACTION" continuation section>[
                {
                    "title": <extract title of author> or null,
                    "last_name": <extract authors last name> or null,
                    "first_name": <extract authors first name> or null,
                    "middle_name": <extract authors middle name> or null,
                    "reporter_type": <extract authors reporter type> or null
                }
            ]
        }
    ],
    "clinical_study": {
        "protocol_number": <extract Protocol No. from the "MANUFACTURER INFORMATION" continuation section> or null,
        "study_description": <extract Study Name from the "MANUFACTURER INFORMATION" continuation section> or null,
        "patient_no": <extract Subject Id from the "MANUFACTURER INFORMATION" section> or null,
        "site_no": <extract Center No. from the "MANUFACTURER INFORMATION" section> or null,
        "registration_no": <extract EudraCT Number from "MANUFACTURER INFORMATION" section> or null
    }
}
```
"""', NOW(), NOW()),

('01K1AN2VDDVKCANACHA85WWCXA', '01K1AGGAEZAC16072DAMTBSXF2', 1, 'en', 0.20, 1.00, 8000, '# Medical CIOMS Form Data Extraction Prompt - **LABORATORY SECTION**

        You are an expert medical document analyst tasked with extracting structured **laboratory test records ONLY** from specific sections of CIOMS forms and medical safety reports.

        ---------------------------------------------------------------------
        GENERAL INSTRUCTIONS
        ---------------------------------------------------------------------
        1. Extract **ONLY** the laboratory test records specified below - no extras.
        2. Output must be **valid JSON (dictionary)** - **no markdown wrappers**.
        3. If a field is missing/blank, use `null`.
        4. IMPORTANT: All the dates in string fields should be extracted in the format `DD-MM-YYYY` or `MM-YYYY` or `YYYY`.
        5. Return a JSON **dictionary** with a single top-level key `"laboratory"`.
        6. `laboratory` MUST be a **LIST**; **each element** is **one test record object**.
        7. **STRICT WARNING:** If the same test appears more than once (e.g., repeated blood pressure measurements), you MUST extract each occurrence as a separate object in the laboratory list. Do NOT merge or deduplicate, even if the test name is identical.
        8. Inside each object, the original field explanations (below) must remain **unchanged**.
        9. Be strict: only include real, explicitly or clearly implied tests. Ignore all other content, even if its medically relevant but not a test.

        ---------------------------------------------------------------------
        TARGET SECTIONS FOR EXTRACTION
        ---------------------------------------------------------------------
        • Section 7+13 (Describe Reaction(s) and Continuation)
        • Sections explicitly labelled **"Laboratory Data", "Lab Results"**, or similar

        ---------------------------------------------------------------------
        EXTRACT ONLY THE FOLLOWING KINDS OF RECORDS
        ---------------------------------------------------------------------
        • Named laboratory tests
        • Immunological tests
        • Microbiological tests
        • Imaging / radiology findings
        • Vital signs
        • "Unspecified test" entries where a test was done but name not given

        ---------------------------------------------------------------------
        EXCLUDE
        ---------------------------------------------------------------------
        • Diagnoses, conditions, symptoms or adverse events
        • Data from outside the target sections above
        • General medical observations that are not a test

        ---------------------------------------------------------------------
        EXPECTED OUTPUT TEMPLATE
        ---------------------------------------------------------------------
        ```json
        {
          "laboratory": <extract the list of tests data, vital signs and laboratory data from "DESCRIBE REACTION" continuation and "LAB DATA" section if any else empty list>[
            {
              "test_name": <extract just test name, imaging result, vital signs, histological finding, or blood/CSF finding from the specified sections, or null>,
              "test_date": <test date if present or null>,
              "normal_value_low": <lower normal value for the test, or null>,
              "normal_value_high": <upper normal value for the test, or null>,
              "comments": <comment on test result> or null,
              "test_result": <result numeric value for the test> or null,
              "result_unit_text": <result unit for the test> or null,
              "test_result_code" Literal["Normal" | "Abnormal" | null]: <result code for the test> or null,
              "result_unstructured_data": <extract whole unstructured result text for the test> or null
            }
            // ⇢ Additional test objects follow …
          ]
        }
        ``` 
        """', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;

-- 7. Insert Extraction Agents with preferred_model
INSERT INTO extraction_agent (id, doc_type_id, code, name, description, prompt_template_id, fallback_chain_id, llm_credential_id, is_active, sequence_no, preferred_model, created_at, updated_at) 
VALUES 
('01K1AQQWB5CMJ0ZHBKXWFG8AJ2', '01K1AGGAEZAC16072DAMTBSXF2', 'PATIENT', 'Agent 1', 'PATIENT', '01K1AN2VDDW1KB5MW0CQG86HG9', '01K1AGGAEZAGKMS9YMZYM1YYWT', '01K1AKWR7BEKTYYF0DJHD24G8Z', true, 1, NULL, NOW(), NOW()),
('01K1AXG2M6NH3ZNQFFMQ2TPD4C', '01K1AGGAEZAC16072DAMTBSXF2', 'AE', 'Agent 2', 'AE', '01K1AN2VDD9N08DFVKG0HZ3K81', '01K1AGGAEZAGKMS9YMZYM1YYWT', '01K1AKWR7BEKTYYF0DJHD24G8Z', true, 2, NULL, NOW(), NOW()),
('01K1AXHV44T90HN18DBGJGRSGQ', '01K1AGGAEZAC16072DAMTBSXF2', 'PRODUCT', 'Agent 3', 'PRODUCT', '01K1AN2VDDTSP43PEGNT6B1BE4', '01K1AGGAEZAGKMS9YMZYM1YYWT', '01K1AKWR7BEKTYYF0DJHD24G8Z', true, 3, NULL, NOW(), NOW()),
('01K1AXK80RN8NNDDCDPKJ53P72', '01K1AGGAEZAC16072DAMTBSXF2', 'CASE', 'Agent 4', 'CASE', '01K1AN2VDDQ3GFE224G1VSB9DW', '01K1AGGAEZAGKMS9YMZYM1YYWT', '01K1AKWR7BEKTYYF0DJHD24G8Z', true, 4, NULL, NOW(), NOW()),
('01K1AXM41JX2KWN07S23HGAY1R', '01K1AGGAEZAC16072DAMTBSXF2', 'LABORATORY', 'Agent 5', 'LABORATORY', '01K1AN2VDDVKCANACHA85WWCXA', '01K1AGGAEZAGKMS9YMZYM1YYWT', '01K1AKWR7BEKTYYF0DJHD24G8Z', true, 5, NULL, NOW(), NOW())
ON CONFLICT (id) DO NOTHING;

