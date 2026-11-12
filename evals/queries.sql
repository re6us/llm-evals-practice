-- Analysis queries over posts.db
-- The database is built from posts_classified2.csv by load_db.py:
-- 50 Hacker News headlines, one classification run, with steps, tokens and cost per row.
--
-- Open with:  sqlite3 posts.db
-- Then:       .headers on
--             .mode column


-- ---------------------------------------------------------------------------
-- 1. Headlines per topic
--
-- Design never appears. The category is defined in the prompt but attracts
-- nothing — either the corpus has no design stories, or the definition fails
-- to pull anything in. An unused category is not free: it sits in a prompt
-- that is sent on every request and gives the model one more thing to weigh.
-- ---------------------------------------------------------------------------

SELECT topic, COUNT(*) AS n
FROM posts
GROUP BY topic
ORDER BY n DESC;


-- ---------------------------------------------------------------------------
-- 2. The five most expensive headlines
--
-- All five took two steps. Cost tracks the agent loop, not the length of the
-- headline or anything about the topic.
-- ---------------------------------------------------------------------------

SELECT title, steps, cost
FROM posts
ORDER BY cost DESC
LIMIT 5;


-- ---------------------------------------------------------------------------
-- 3. Cost per topic
--
-- The totals mirror the counts, because cost per row barely varies — so the
-- sum answers a budgeting question rather than an analytical one.
-- The average is the interesting column: Other is the most expensive topic
-- per headline, which fits the idea that Other means "could not decide" and
-- sends the model looking for evidence.
-- Sample sizes are small (Other n=1, Science n=2) — treat as a hypothesis.
-- ---------------------------------------------------------------------------

SELECT topic,
       COUNT(*) AS n,
       ROUND(SUM(cost), 4) AS total_cost,
       ROUND(AVG(cost), 5) AS avg_cost
FROM posts
GROUP BY topic
ORDER BY avg_cost DESC;


-- ---------------------------------------------------------------------------
-- 4. How often each topic needs the page fetched
--
-- steps = 1 means the headline was enough; steps = 2 means the agent opened
-- the linked page first. The ordering here is identical to average cost,
-- which confirms cost is a function of step count and nothing else.
--
-- Cheap topics are the self-identifying ones (Hardware, AI); expensive ones
-- require judgement (Other, Science).
-- ---------------------------------------------------------------------------

SELECT topic,
       COUNT(*) AS n,
       ROUND(AVG(steps), 2) AS avg_steps
FROM posts
GROUP BY topic
ORDER BY avg_steps DESC;


-- The same effect stated directly: two-step headlines cost 2.15x more.
-- 16 of 50 headlines take two steps and account for roughly half the spend.

SELECT steps,
       COUNT(*) AS n,
       ROUND(AVG(cost), 5) AS avg_cost,
       ROUND(SUM(cost), 4) AS total_cost
FROM posts
GROUP BY steps
ORDER BY avg_cost DESC;


-- ---------------------------------------------------------------------------
-- 5. Rows escalated for human review
--
-- All four are confidence = low. The topic = 'ERROR' half of the escalation
-- condition has never fired, so it remains untested.
--
-- Note: needs_review is stored as the text 'True' / 'False', not as a boolean.
-- Python wrote it through the CSV and SQLite kept it as text, so the
-- comparison needs quotes.
-- ---------------------------------------------------------------------------

SELECT title, topic, confidence, needs_review
FROM posts
WHERE needs_review = 'True';


-- What values actually live in a column — the first thing to run when the
-- type or the contents of a field are unclear.

SELECT needs_review, COUNT(*) AS n
FROM posts
GROUP BY needs_review;


-- ---------------------------------------------------------------------------
-- 6. Which topics score highest on Hacker News
--
-- The first question here about the subject matter rather than the pipeline.
--
-- Averages are pulled by outliers, so min and max are shown alongside: AI
-- averages 195 points but ranges from 16 to 895 across 8 headlines, so the
-- lead comes from one viral post rather than consistent interest.
-- A median would be the right statistic; SQLite has none built in.
--
-- This is also a single snapshot of one day's front page. It says what did
-- well that day, not what does well on Hacker News.
-- ---------------------------------------------------------------------------

SELECT topic,
       COUNT(*) AS n,
       ROUND(AVG(score)) AS avg_score,
       MIN(score) AS min_score,
       MAX(score) AS max_score
FROM posts
GROUP BY topic
ORDER BY avg_score DESC;
