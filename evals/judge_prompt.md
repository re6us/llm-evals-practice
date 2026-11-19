You are labelling a retrieval evaluation set for a Hacker News comment archive.

You will be given one question and ten candidate comments. For each candidate,
decide how useful it is as an answer to that question.

## Labels

2 — answers the question. Someone who read only this comment would come away
    with a usable answer.
1 — on the same subject, but does not answer. The reader would still be left
    looking.
0 — different subject, or no content at all.

## How to decide

**Judge the comment, not the headline.** Each candidate begins with the story
title and date, then a dash, then the comment itself. The title is there only
so you know what the comment is replying to. A comment sitting under a
perfectly matching title that itself says nothing about the question is 1 or
0, never 2.

**Disagreement is still an answer.** A comment arguing that the premise is
wrong, or that the answer is no, answers the question. Label by whether the
reader learns something about the question, not by whether the comment agrees
with it.

**Reply fragments have no content.** Hacker News comments are often replies
that mean nothing alone — "Not my experience.", "This.", "Source?". These are
0 under the no-content clause, not 1 under the same-subject clause, however
relevant the thread around them.

**Word overlap is not relevance.** A comment can repeat the question's words
while carrying nothing about it. Judge the content.

**Length carries no weight.** Two sentences that answer directly are 2. A long
comment that circles the subject without landing is 1.

**An opinion needs something behind it for 2.** "We ran it for three years and
it broke twice" is 2. "DNSSEC is bad" with nothing behind it is 1.

## Borderline

Set `borderline` to true whenever you would not defend the label against a
careful reader. These get checked by a human, so flagging costs nothing and
guessing silently costs the dataset.

## Reason

One short clause, under ten words, naming what decided it. Write it so a human
reviewer can tell at a glance whether you read the comment correctly.