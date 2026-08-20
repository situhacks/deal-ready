# The ten metrics, and how a CIM hides them

Written for someone learning this domain by construction rather than from a desk. Each
metric gets the same three questions: what it is, why a permanent-capital buyer prices
on it, and how a memorandum can be truthful about it while still leaving you with the
wrong impression.

That third question is the useful one. A CIM is a marketing document produced by a
seller's advisor. It is not usually false. It is *arranged* — and knowing the
arrangements is most of what separates a screen from a spreadsheet.

**A note on who is reading.** Everything here assumes a buy-and-hold acquirer: one that
intends to own the business permanently, with no exit to underwrite. That single fact
reorders every metric below. A growth investor needs a step-up in five years and will
pay for momentum. A permanent-capital buyer needs the business to still be here in
twenty, and pays for durability. Metrics that look sophisticated under the first thesis
can be actively misleading under the second — see Rule of 40 at the end.

---

## 1. ARR — Annual Recurring Revenue

**What it is.** Contracted subscription revenue, annualised. The number the multiple is
usually applied to.

**Why it prices.** It is the closest thing to a forward view of the business that a
buyer can underwrite. Everything else adjusts it.

**How a CIM arranges it.** By widening what counts as recurring. Implementation fees,
training days, mandatory annual "support" that is really a licence, one-time data
migration — bundle enough of that into the headline and a $7M business presents as
$11M. Ridgeline in this corpus does exactly that.

The check is arithmetic and it is the first one to run: **does stated ARR equal
annualised MRR?** If exit-month MRR times twelve is materially below stated ARR, the
difference is non-recurring revenue sitting inside the headline. `rules.py R1` flags a
gap above 5%.

---

## 2. MRR — Monthly Recurring Revenue

**What it is.** The subscription run-rate in the most recent month.

**Why it prices.** It is harder to dress up than ARR because it is a point-in-time
measure. A one-time fee inflates a month; it does not inflate a run-rate that has to be
true again next month.

**How a CIM arranges it.** By choosing the month. An exit month that happens to follow
a large go-live, or precedes a known churn event, is a legitimate figure and an
unrepresentative one. Ask for the twelve-month series, not the exit month.

---

## 3. Recurring revenue as a share of total

**What it is.** What proportion of all revenue actually repeats without new work.

**Why it prices.** This is the metric that decides whether you are buying software or
a consultancy with software attached. Services revenue is real revenue, but it is
linear in headcount, it carries lower margins, and it does not compound. A buyer pays a
software multiple for software revenue and something closer to a services multiple for
the rest.

**How a CIM arranges it.** By omission, usually. A memorandum that talks about ARR
constantly and never states the recurring share has told you something.

**The floor exists for a reason.** Below roughly 80%, the delivery organisation is the
business. Ridgeline runs 58% with a 39-person services team, and the tell is right there
in the narrative: configuration is performed by the vendor rather than the customer.

---

## 4. GRR — Gross Revenue Retention

**What it is.** Of the revenue you had a year ago, how much is still here — counting
only losses. Downgrades and cancellations pull it down; expansion is excluded entirely.
**It cannot exceed 100%.**

**Why it prices.** For a permanent-capital holder this is the single most important
metric in the document. It answers whether the base leaks. A business that keeps 96% of
its revenue each year is a different asset from one that keeps 81%, and the difference
compounds every year you own it — which, for this buyer, is every year.

**How a CIM arranges it.** Two ways, and the second is the common one:

- **Reporting net retention and calling it gross.** If you see a "gross retention" figure
  above 100%, this has happened. `rules.py R5` treats it as a definition error rather
  than a triumph, because that is what it is.
- **Putting it in a chart with no data labels.** In this corpus GRR and NRR live only in
  an unlabelled trend line — which is why a text-only pipeline scores 0% on them and
  a 1B vision model, which reads printed labels but cannot read a value off an axis,
  also scores 0%. That is not a hypothetical; it is measured in
  [`reports/layer_p.md`](../reports/layer_p.md).

---

## 5. NRR — Net Revenue Retention

**What it is.** The same cohort, but counting expansion, upsell and price increases as
well as losses. Can exceed 100%.

**Why it prices.** It tells you whether the installed base grows on its own. Above 100%
the business compounds without winning a single new logo, which is the most durable
growth there is.

**How a CIM arranges it.** By leading with it and letting the reader assume it means
customers are happy. NRR of 108% with GRR of 81% describes a business losing customers
steadily while extracting more from the ones who stay. Both numbers are true. Only the
pair is informative — **read them together or not at all.**

---

## 6. Gross margin

**What it is.** Revenue less the cost of delivering it — hosting, support, third-party
licences, and the services staff required to keep customers live.

**Why it prices.** It separates a software company from a company that sells software.
Sub-65% margins in a business calling itself SaaS usually mean either a services-heavy
delivery model or infrastructure costs that never came down.

**How a CIM arranges it.** By what sits above the line. Support staff classified as R&D
rather than COGS lifts margin without changing a thing about the business. If margin
looks unusually good for the vertical, ask where support headcount is booked.

---

## 7. EBITDA

**What it is.** Earnings before interest, tax, depreciation and amortisation. In
practice, **adjusted** EBITDA — the seller's view after add-backs.

**Why it prices.** For a buyer with no exit, profitability is not a milestone on a path
to something else. It is the thing being purchased.

**How a CIM arranges it.** In the add-backs, always. "One-time" costs that recur
annually, owner compensation normalised to a number no successor would accept,
transaction preparation fees, a legal matter described as non-recurring. Every add-back
is a claim about the future, and the diligence question is the same each time: *would
this cost genuinely not exist under new ownership?*

---

## 8. Customer concentration — largest customer

**What it is.** The share of ARR resting on one logo.

**Why it prices.** One departure removes that share of revenue in a single renewal
cycle. It does not usually kill a deal; **it reprices one.** A buyer underwriting a
34% single-customer concentration is buying a different risk profile at the same
multiple, and should not.

**How a CIM arranges it.** By showing the distribution as a chart rather than a table,
and by grouping. "Top 5 customers" as a single bar conceals whether that is five even
relationships or one giant and four small ones.

**The diligence follow-through matters more than the number.** If concentration is
high, the change-of-control and assignment clauses in those contracts become the first
thing legal reads — because the risk is not that the customer is large, it is that the
customer can walk *because you bought the company*.

---

## 9. Customer concentration — top five

**What it is.** The same question one ring wider.

**Why it prices.** It tells you whether revenue quality rests on a handful of
relationships that an ownership change can disturb — and whether those relationships
belong to the company or to a founder who is leaving.

**How a CIM arranges it.** By reporting it only as a percentage and never as a list.
Percentages hide whether the five are in one vertical, one geography, or one
procurement cycle.

---

## 10. Year-over-year growth

**What it is.** Revenue growth against the prior year.

**Why it prices — and why less than you would think.** For a permanent-capital buyer,
growth is welcome but it is not the thesis. A 2%-growth business with 96% retention in
a niche nobody else wants to serve can be a better permanent asset than a 40%-growth
business burning cash to sustain it.

**How a CIM arranges it.** By choosing the window and the basis. Growth measured from a
trough, or on bookings rather than recognised revenue, or including an acquisition.

---

## The one to be careful with: Rule of 40

**What it is.** Growth rate plus EBITDA margin. Above 40 is conventionally healthy.

**Why it is in this repo, and why it is scored at zero weight.**

Rule of 40 asks whether a company is trading margin for growth at an acceptable rate.
That is the right question if you are underwriting a step-up at exit in five years — it
tells you whether the burn is buying something.

**A permanent-capital buyer is not underwriting an exit.** It wants a profitable,
sticky, slow-growing business it can hold indefinitely. Such a business fails Rule of 40
*by construction*: modest growth plus healthy margin lands in the thirties.

This was not a theoretical concern. During development the rule fired on **all five
targets, including the deliberately clean one** — which is the tell that a metric has
been imported from the wrong thesis. Scoring a permanent-capital target against a
venture yardstick would have ranked the portfolio backwards.

So it is computed, reported as context, and never allowed to move the score. Keeping
it visible is honest; letting it vote would not be.

**The general lesson, which outlasts this metric:** a benchmark carries the assumptions
of the investor who invented it. Before adopting one, ask whose thesis it encodes — and
whether that is your thesis.
