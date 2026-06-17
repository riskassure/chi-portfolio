-- Reset all images back to a baseline display count of 0
UPDATE photography_catalog SET display_count = 0;

-- Clear out historical dates so your priority sort treats them all equally as brand new
UPDATE photography_catalog SET last_displayed_date = NULL;

-- Keep exactly 3 initial images flagged as active so your homepage loads clean
UPDATE photography_catalog SET is_currently_displayed = 0;
UPDATE photography_catalog SET is_currently_displayed = 1 WHERE image_id IN (1, 2, 3);