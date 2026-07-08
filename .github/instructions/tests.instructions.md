---
applyTo: "tests/**"
---

# Unit Test Standards

Whenever you are asked to create, generate, or update unit tests, you must strictly adhere to the following rules:

## 1. Scope Limitation
- Write ONLY pure unit tests. Do not write integration or end-to-end tests.
- Isolate the target class or function completely from external infrastructure.

## 2. Test Value & Volume Balance
- Maximize logical confidence while keeping the test suite lean, lightweight, and fast to execute.
- Quality over quantity: Focus exclusively on high-impact paths (boundaries, core state mutations, and complex branching logic).
- Do not write redundant tests. If a behavior is already verified, do not add more tests for it just to increase line count.

## 3. Test Categorization
- **Happy Path**: Verify standard successful execution flows using valid, expected inputs.
- **Unhappy Path**: Verify graceful handling of invalid inputs, out-of-bounds conditions, and ensure that the precise custom exceptions are raised.

## 4. Efficiency via Parameterization
- Heavily utilize parameterized tests (e.g., `@pytest.mark.parametrize`) to test multiple input variations—both valid and invalid—within a single test function.
- Do not duplicate test logic across multiple functions if they can be unified via parameters.

## 5. Structural Standard
- Follow the **Arrange-Act-Assert (AAA)** pattern strictly.
- Keep test bodies short, readable, and free of unnecessary setup boilerplate.

## 6. Prohibited Testing Practices
- Do NOT use `monkeypatch` or dynamically alter runtime code or imports during execution.
- If dependencies must be controlled, use clean Dependency Injection or standard unit test mocks.

## 7. Absolute Prevention of Over-Testing (Anti-Hyper-Coverage)
- Strictly avoid combinatorial explosion. Do not generate hundreds or thousands of tests to brute-force every possible numeric permutation.
- Maintain a maintainable test suite size. For any given component, target the minimum number of high-quality tests required to achieve full logical branch coverage.
- Priority: Execution speed and low maintenance overhead are as important as coverage. If a test adds more maintenance weight than bug-catching value, omit it.
