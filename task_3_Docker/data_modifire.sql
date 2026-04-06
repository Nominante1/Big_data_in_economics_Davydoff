
SELECT * FROM user_logs ORDER BY RANDOM() LIMIT 10

/*
SELECT 
	AVG(s_all_avg)
FROM USER_LOGS
*/

--Обязательные преобразования (удаление точек + перевод в real(float4))
UPDATE USER_LOGS SET s_all_avg = REPLACE(s_all_avg, ',', '.') WHERE s_all_avg LIKE '%,%';
UPDATE USER_LOGS SET s_course_viewed_avg = REPLACE(s_course_viewed_avg, ',', '.') WHERE s_course_viewed_avg LIKE '%,%';
UPDATE USER_LOGS SET s_q_attempt_viewed_avg = REPLACE(s_q_attempt_viewed_avg, ',', '.') WHERE s_q_attempt_viewed_avg LIKE '%,%';
UPDATE USER_LOGS SET s_q_attempt_viewed_avg = REPLACE(s_q_attempt_viewed_avg, ',', '.') WHERE s_q_attempt_viewed_avg LIKE '%,%';
UPDATE USER_LOGS SET s_a_course_module_viewed_avg = REPLACE(s_a_course_module_viewed_avg, ',', '.') WHERE s_a_course_module_viewed_avg LIKE '%,%';
UPDATE USER_LOGS SET s_a_submission_status_viewed_avg = REPLACE(s_a_submission_status_viewed_avg, ',', '.') WHERE s_a_submission_status_viewed_avg LIKE '%,%';

ALTER TABLE USER_LOGS ALTER COLUMN s_all_avg TYPE REAL USING s_all_avg::REAL;
ALTER TABLE USER_LOGS ALTER COLUMN s_course_viewed_avg TYPE REAL USING s_course_viewed_avg::REAL;
ALTER TABLE USER_LOGS ALTER COLUMN s_q_attempt_viewed_avg TYPE REAL USING s_q_attempt_viewed_avg::REAL;
ALTER TABLE USER_LOGS ALTER COLUMN s_a_course_module_viewed_avg TYPE REAL USING s_a_course_module_viewed_avg::REAL;
ALTER TABLE USER_LOGS ALTER COLUMN s_a_submission_status_viewed_avg TYPE REAL USING s_a_submission_status_viewed_avg::REAL;
*/
--Непонятно, надо или не надо

ALTER TABLE USER_LOGS ALTER COLUMN date_vatt TYPE DATE USING TO_DATE(date_vatt, 'DD.MM.YYYY');
ALTER TABLE USER_LOGS ALTER COLUMN kurs TYPE INT USING kurs::integer;
ALTER TABLE USER_LOGS ALTER COLUMN leveled TYPE INT USING leveled::integer;
ALTER TABLE USER_LOGS ALTER COLUMN name_formopril TYPE INT USING name_formopril::integer;
ALTER TABLE USER_LOGS ALTER COLUMN name_osno TYPE INT USING name_osno::integer;
ALTER TABLE USER_LOGS ALTER COLUMN namer_level TYPE INT USING namer_level::integer

--Получение среднего значения
SELECT 
	AVG(s_all_avg)
FROM USER_LOGS

--Вывод всех типов столбцов
SELECT column_name, udt_name 
FROM information_schema.columns 
WHERE table_name = 'user_logs';
