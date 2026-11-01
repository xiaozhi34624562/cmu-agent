# Email priority rubric

This is the rubric the gold labels in `tests/fixtures/priority_gold.json`
follow. Each email gets exactly one of three labels: `urgent`, `normal`, or
`ignore`.

Judge every email from the point of view of the person it is addressed to
(the `to` field), at the time it was sent. The question is what that person
should do with the message, not how important the topic is to the company.

## urgent

The recipient has to act or decide soon. Two things must both be true:

1. The email asks the recipient to do something, or reports a live problem
   that the recipient is responsible for (an outage, a failed payment, a
   customer or manager escalating an issue).
2. There is time pressure: the email states or clearly implies that the
   action is needed the same day, the next working day, or by a stated
   deadline no more than two working days away.
   A working day is Monday to Friday, counted from the email's date.

Examples:

- "The bank rejected this morning's wire. I need you to approve the
  corrected one by 1:00 PM or we pay a late penalty."
- "The customer's CFO is threatening to cancel. Can you call him before
  4:00 today?"

## normal

Legitimate work or personal mail that was written for this recipient or for
a small working group, with no deadline in the next two working days. This
covers status updates and FYIs, ordinary questions, documents sent for
review without a near deadline, meeting scheduling for later dates, replies
in an ongoing discussion, and personal notes from friends or family.

Examples:

- "Attached is the draft term sheet. Let me know if you have comments
  before our meeting the week after next."
- "Thanks for lunch yesterday. Are you still coming to the lake in
  August?"

## ignore

Mail the recipient can leave unread at no cost: advertising and spam from
vendors, newsletters and news digests, announcements sent to large employee
lists (events, training offerings, facilities notices), and automated
notifications that do not require the recipient to do anything.

Examples:

- "This week only: 40% off all standing desks. Reply REMOVE to
  unsubscribe."
- "To all employees: the annual bake sale is in the lobby on Friday from
  11:00 to 1:00."

## Deciding between two labels

- The wording does not decide the label. An email with "URGENT" in the
  subject that asks nothing of the recipient is not `urgent`. A calm email
  that says "I need your signature by 3:00 PM today" is `urgent`.
- A request with a deadline more than two working days away, or with no
  deadline, is `normal`.
- Mass mailings and advertising are `ignore` even when they use words such
  as "act now" or "important", because nothing is asked of this recipient in
  particular.
- An automated notice that asks this specific recipient to act (for
  example, an expense report waiting for their approval) is `normal`, or
  `urgent` if it states a deadline within two working days.
- A short personal or social message from someone the recipient knows is
  `normal`, not `ignore`.

## How the gold labels were made

Candidate emails were labeled independently by two models that were given
this rubric, and each email was then read against the rubric a third time
during the data build. An email is in the gold set only if all three
readings agreed on its label. Emails with any disagreement were left out, so
the gold set contains the clearer cases.
