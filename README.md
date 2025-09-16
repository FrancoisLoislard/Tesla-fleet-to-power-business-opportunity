# ⚡ Tesla Fleet to Power Business Opportunity

This project provides a **Streamlit dashboard** that estimates the potential **power trading opportunity** for Tesla, based on its EV fleet growth, battery capacity, and supercharger network expansion.

The app combines **historical sales data**, **battery specifications**, and **forecast parameters** (growth rate, retirement rate, forecast horizon) to project the aggregated fleet capacity (in MWh). It then links this capacity to a simplified business opportunity model.

---

## 🚀 Features

- **Fleet capacity modeling**  
  Computes the potential energy capacity of the Tesla EV fleet based on sales and battery specifications.

- **Forecasting**  
  Adjustable parameters for sales growth, retirement rate, and number of forecast years.

- **Supercharger expansion**  
  Visualizes the historical growth of Tesla's supercharger network.

- **Business opportunity estimation**  
  Provides an indicative estimate of the potential market value of Tesla’s fleet capacity in the power trading market.

- **Clean architecture**  
  - `app.py` → Streamlit UI and plots  
  - `utils.py` → Data loading and fleet capacity calculation logic  
  - `style.py` → Centralized custom CSS styling  

---

## 📊 Example Dashboard

- Line chart of fleet capacity over time (historical + forecasted).  
- Bar chart of Tesla’s supercharger growth.  
- Key metrics for estimated market opportunity.
