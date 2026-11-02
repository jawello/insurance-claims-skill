# MetLife Cyprus group claims

Check these against the current form and your own policy, since terms change.

- Email: claimscyprus@metlife.com. Post: MetLife Europe d.a.c. (Cyprus Branch), Claims Department, 38 Kennedy Avenue, 1087 Nicosia.
- Originals: Part F says originals are sent within 30 days of submission. If that is not feasible, keep them, because MetLife can request them for up to 6 years after settlement.
- The main insured submits claims for dependents too.
- The claim number is stamped in the browser when the group claim form link is clicked on https://www.metlife.com.cy/en/useful-documents/ (Claims section, English Version). curl of the PDF URL gives an unnumbered form. `scripts/download_form.py` does the click.

## Form fields

`scripts/fill_form.py` handles the gender, TOTAL and date-comb issues below.

- Part A gender widgets are mislabelled: `5 Gender` is the Male box, and `Male` is the Female box. Part B has the same swap in `5 Gender_2` and `Male_2`. In the values file, pass `"gender"` for Part A and `"main_insured_gender"` for Part B, each `"male"` or `"female"`, instead of these field names.
- Most field names do not match their labels. Part A: `policy` first name, `name` surname, `identity` ID or passport, `Y` date of birth. Part B: `Text8` policy number, `Text9` company, `Text10` first name, `Y_2` date of birth, `Text11` surname, `Text12` ID or passport, `Text13` telephone, `10 Email_2` email. Part C: `Text15` description of illness, `Text16` first symptoms, `Name of Doctors that were consulted 1` doctor, `Y_3` its date, `Text20` GHS visit. Part D rows: `Text17.0.N` diagnosis, `Text17.2.N` amount. Part E: `Text21` doctor, `Text22` clinic, `Text23` doctor's telephone, `Please provide full details of the symptomsmedical condition 1` symptoms, `Y_7` date first presented, `Text29` further treatment. Part F: `Claimants name_2`.
- Date fields are DDMMYY combs. `Y_9`, `Y_10` and `Y_11` have MaxLen 5 and need 6.
- TOTAL has a JavaScript auto-sum that zeroes text amounts, so it is removed.
- Text renders at 10 pt with no shrink, so long values do not fit.
- Part D "Other" rows have no description field: use `Text17.x.11+`, check `Check Box19.11.0`, and add an overlay label at x=112.
- Dental has no Part D row, so use the "Other" rows.
- Surgery with admission: split it into accommodation, surgeon and anaesthetist rows instead of "surgical operations not requiring hospitalization". Outpatient and inpatient limits can differ a lot, so check your certificate.
