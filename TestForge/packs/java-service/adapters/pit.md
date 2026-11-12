# PIT (pitest)

- Mutation testing for Java; Maven plugin:
  `mvn org.pitest:pitest-maven:mutationCoverage`.
- TestForge `gate` can parse `target/pit-reports/mutations.xml` with `mutation.parser: "pit-xml"`.
- Do not chase 100%; classify surviving mutants as real gap, equivalent mutant, or unreachable.
- Run on changed classes in CI; full-repo mutation is expensive.
