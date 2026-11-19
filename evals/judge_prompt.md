You are labelling a retrieval evaluation set for a Hacker News comment archive.

You will be given one question and ten candidate comments. For each candidate,
decide how useful it is as an answer to that question.

## Labels

The retriever hands five comments to a model, which writes one answer from all
of them together. So the question for each candidate is not whether it answers
on its own, but whether the answer would be worse without it.

2 — carries something the answer would use: a fact, a number, a first-hand
    experience, a mechanism, or a clear position with a reason behind it.
1 — about the same subject, but carries nothing the answer would use.
0 — a different subject, or nothing said at all.

## The test for 2

Could you write one sentence of the answer and cite this comment for it?

    yes  →  "Deploying it across 200 zones produced two outages from expired
             signatures."                                              → 2
    no   →  the best you could write is "someone discussed this"       → 1

A comment that gives part of the answer is 2. It does not have to be complete,
because four other comments arrive with it. But it has to carry something, not
merely be adjacent to the subject.

## Where the line sits

Question: is DNSSEC worth deploying in practice

    2  "We signed 200 zones in 2019 and have had two outages since, both from
        expired signatures."                 a fact you would cite
    2  "Not worth it - the attack it stops is rarer than the misconfigurations
        it causes."                          a position with a reason
    1  "DNSSEC is a mess."                   a position with nothing behind it
    1  "Your old post about this has been answered many times already."
                                             about the argument, not the question
    0  "In theory, theory and practice are the same."     says nothing
    0  "Source?"                                          says nothing

Two different reasons end up at 0, and they are not the same as 1:

    1  the comment says something about the subject, but nothing usable
    0  the comment is about a different subject, OR says nothing at all

## How to decide

**Judge the comment, not the headline.** Each candidate begins with the story
title and date, then a dash, then the comment itself. The title is there only so
you know what the comment is replying to. A comment sitting under a perfectly
matching title that itself carries nothing about the question is 1 or 0, never 2.

**Disagreement is still an answer.** A comment arguing that the premise is wrong,
or that the answer is no, carries something the answer would use. Label by what
the comment contributes, not by whether it agrees with the question.

**Empty replies say nothing.** Hacker News comments are often replies that mean
nothing alone — "Not my experience.", "This.", "Source?". These are 0, however
relevant the thread around them.

**Word overlap is not relevance.** A comment can repeat the question's words
while carrying nothing about it. Judge the content.

**Length carries no weight.** Two sentences that carry a fact are 2. A long
comment that circles the subject without landing is 1.

## Borderline

Set `borderline` to true whenever you would not defend the label against a
careful reader. These get checked by a human, so flagging costs nothing and
guessing silently costs the dataset.

## Reason

One short clause, under ten words, naming what decided it. Write it so a human
reviewer can tell at a glance whether you read the comment correctly.