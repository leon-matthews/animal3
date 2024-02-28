
# Animal3

Core application for Digital Advisor Django projects.

## Dependency Management

Depend only on Django and standard Python libraries. Use only features from
oldest version of Python running on any of our servers. Third-party code can
only be imported via the `adapters` app (which should maybe pulled out as
`apis` was), and only after great effort is taken to ensure that running tests,
etc., without dependency installed is supported.
