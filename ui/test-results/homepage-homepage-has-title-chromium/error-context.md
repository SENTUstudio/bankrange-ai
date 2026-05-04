# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: homepage.spec.ts >> homepage has title
- Location: src/tests/e2e/homepage.spec.ts:3:1

# Error details

```
Error: expect(locator).toContainText(expected) failed

Locator: locator('h1')
Expected substring: "Tactical Map"
Timeout: 5000ms
Error: element(s) not found

Call log:
  - Expect "toContainText" with timeout 5000ms
  - waiting for locator('h1')

```

# Page snapshot

```yaml
- generic [ref=e2]:
  - generic [ref=e3]:
    - generic [ref=e4]: BankRange STOPPED RECONNECTING...
    - generic [ref=e5]:
      - generic [ref=e6]: EPS 0.0
      - generic [ref=e7]: WS 0
      - generic [ref=e8]: MULT 1.0x
  - generic:
    - generic:
      - generic:
        - region "Map" [ref=e9]
        - group [ref=e10]:
          - generic "Toggle attribution" [ref=e11] [cursor=pointer]
          - generic [ref=e12]:
            - link "MapLibre" [ref=e13] [cursor=pointer]:
              - /url: https://maplibre.org/
            - text: "| ©"
            - link "CARTO" [ref=e14] [cursor=pointer]:
              - /url: https://carto.com/about-carto/
            - text: ", ©"
            - link "OpenStreetMap" [ref=e15] [cursor=pointer]:
              - /url: http://www.openstreetmap.org/about/
            - text: contributors
  - generic [ref=e16]:
    - generic [ref=e17]:
      - heading "Controls" [level=3] [ref=e18]
      - text: v2.4
    - button "DEPLOY" [ref=e20]
    - generic [ref=e21]:
      - generic [ref=e22]: EPS Multiplier 1.0x
      - slider [ref=e23]: "1"
    - generic [ref=e24]:
      - generic [ref=e25]:
        - generic [ref=e26]: EST. EPS
        - generic [ref=e27]: "0.0"
      - generic [ref=e28]:
        - generic [ref=e29]: WORKSTATIONS
        - generic [ref=e30]: "0"
    - generic [ref=e31]: "ERR: Failed to fetch"
```

# Test source

```ts
  1 | import { test, expect } from "@playwright/test";
  2 | 
  3 | test("homepage has title", async ({ page }) => {
  4 |   await page.goto("/");
> 5 |   await expect(page.locator("h1")).toContainText("Tactical Map");
    |                                    ^ Error: expect(locator).toContainText(expected) failed
  6 | });
  7 | 
```