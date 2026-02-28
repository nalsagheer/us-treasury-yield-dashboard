\# US Treasury Yield Curve Analysis Dashboard



\## Project Overview



This project presents an interactive financial dashboard designed to analyze the behavior of the US Treasury Yield Curve across three key maturities: 5-year, 10-year, and 30-year government bonds. The objective is to explore yield levels, volatility patterns, maturity relationships, and curve dynamics in order to better understand fixed income market behavior over time.



The dashboard allows users to interactively select time horizons and observe how interest rate structures evolve, offering both descriptive analytics and structural insights into the term structure of interest rates.



---



\## Business \& Analytical Objective



The primary analytical goal of this project is to examine:



\- How US Treasury yields move over time.

\- The relationship between short- and long-term maturities.

\- The stability (volatility) of different bond maturities.

\- Whether the yield curve exhibits normal or inverted behavior.



Understanding yield curve dynamics is critical in financial markets, as slope changes and inversions are often associated with macroeconomic expectations and potential economic slowdowns.



---



\## Data Source



The dataset is obtained from Yahoo Finance using the `yfinance` API.  

The following Treasury indices are used:



\- US 5-Year Treasury Yield (^FVX)

\- US 10-Year Treasury Yield (^TNX)

\- US 30-Year Treasury Yield (^TYX)



Data is fetched dynamically at daily frequency and processed within the Streamlit application.



---



\## Methodology



The analysis consists of several core components:



\### 1. Yield Level Analysis

Daily yield data is collected and visualized to observe long-term trends and structural movements across maturities.



\### 2. Yield Curve Snapshot

The latest available data point is used to construct the current yield curve, illustrating the shape of the term structure.



\### 3. Curve Slope (10Y - 5Y)

The difference between 10-year and 5-year yields is computed to evaluate the slope of the yield curve.  

\- A positive slope indicates a normal curve.

\- A negative slope indicates an inverted curve, often considered a recession signal.



\### 4. Volatility Measurement

Daily yield changes are calculated, and rolling standard deviation is applied to measure yield volatility across maturities.



\### 5. Correlation Analysis

Correlation of daily yield changes is computed to understand how different maturities move relative to one another.



---



\## Key Insights



\- Long-term maturities generally exhibit higher average yield levels.

\- Shorter maturities often demonstrate relatively higher short-term volatility.

\- Yield curve slope fluctuations highlight periods of tightening or flattening.

\- Strong positive correlations (typically above 0.9) indicate synchronized movement across maturities.



---



\## Tools \& Technologies Used



\- Python

\- Pandas (data manipulation)

\- NumPy (numerical operations)

\- yfinance (data source API)

\- Plotly (interactive visualizations)

\- Streamlit (dashboard framework)



---



\## Assumptions \& Limitations



\- Data is sourced from Yahoo Finance and may be subject to availability limitations.

\- Analysis is performed at daily frequency only.

\- Macroeconomic variables (inflation, GDP, Fed policy decisions) are not incorporated.

\- The project focuses on descriptive analytics rather than predictive modeling.



---



\## How to Run Locally



```bash

pip install -r requirements.txt

streamlit run app.py

