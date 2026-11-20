You are labelling a retrieval evaluation set for a Hacker News comment archive.

You will be given one question and ten candidate comments. For each candidate,
decide how useful it is as an answer to that question.

Each candidate is shown in two parts:

    Thread title: the title of the story the comment was posted under
    Comment: the comment itself

The title is context only, so you know what the comment is replying to.
Label the comment.

## Labels

The retriever hands five comments to a model, which writes one answer from all
of them together. So the question for each candidate is not whether it answers
on its own, but whether the answer would be worse without it.

2 — carries something the answer would use: a fact, a number, a first-hand
    experience, a mechanism, or a clear position with a reason behind it.
1 — about the same subject, but carries nothing the answer would use.
0 — a different subject, or nothing said at all.

## The test for 2

Could you write one sentence of the answer and cite this comment for it,
using only what the comment itself says?

    yes  →  "Deploying it across 200 zones produced two outages from expired
             signatures."                                              → 2
    no   →  the best you could write is "someone discussed this"       → 1

A comment that answers part of the question is 2. If the question has two
sides (quality and speed, cost and benefit) and the comment speaks directly to
one of them, that is enough, because four other comments arrive with it. But
it has to carry something about the question itself, not merely sit next to it.

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

## What is not a 2

Five patterns look like answers and are not. Each is 1 when the comment is
about the same subject, otherwise 0.

**A step the comment does not take.** If reaching the question needs a link
the comment never states, the link is yours, not the comment's.
Question: can this startup survive a funding drought.
Comment: "Their product is the best in the category."
From product quality to survival is a step the comment does not take → 1.

**A broader claim than the question.** A statement about technology, companies
or software in general is not a 2 for a question about a specific tool,
company or case, unless the comment itself applies it to that case.
Question: does Copilot speed up code review.
Comment: "Automation rarely saves time until teams change their process."
Applying the general claim to Copilot is a step the comment does not take → 1.

**Restating the premise.** When the question assumes something, a comment that
confirms the assumption does not answer the question.
Question: is a refurbished laptop with a weak battery still worth buying.
Comment: "The battery on these lasts two hours at most."
The weak battery is the premise; the question is about worth → 1.

**Facts on a neighbouring topic.** Concrete figures near the subject do not
answer a narrower question.
Question: how much does the city spend on road repair.
Comment: "The city's total budget is $4B this year, up 10%."
No road repair figure → 1.
If your reason needs "but not" or "though not", the label is not 2.

**A fact from the title.** A fact that appears only in the thread title does
not count, however well it answers the question. Label only what the comment
says.

## How to decide

**Disagreement is still an answer.** A comment arguing that the premise is wrong,
or that the answer is no, carries something the answer would use. Label by what
the comment contributes, not by whether it agrees with the question.

**Empty replies say nothing.** Hacker News comments are often replies that mean
nothing alone — "Not my experience.", "This.", "Source?". These are 0, however
relevant the thread around them.

**Word overlap is not relevance.** A comment can repeat the question's words
while carrying nothing about it. Judge the content.

**Length carries no weight.** Two sentences that carry a fact are 2. A long
comment that circles the subject without landing is 1. A long comment with one
usable line among many is 2.

## Borderline

Set `borderline` to true whenever you would not defend the label against a
careful reader. These get checked by a human, so flagging costs nothing and
guessing silently costs the dataset.

## Reason

One short clause, under ten words, naming what decided it. Write it so a human
reviewer can tell at a glance whether you read the comment correctly.
