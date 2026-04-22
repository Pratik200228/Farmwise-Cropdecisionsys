# FarmWise AI: Final Project Report
## A Decoupled Multi-Agent Decision Support System for Small-Scale Agriculture

**Date**: April 22, 2026  
**Course**: Applied Artificial Intelligence  
**Team**:  
- **Swabhiman Paudel**: Project Lead & AI Agent Developer  
- **Prabin B.K.**: Integration Lead & Data Engineer  
- **Pratik Pokharel**: UI/UX Designer & Front-End Developer  
- **Sujal Thapa**: System Architect & Documentation Lead  

---

### 1. Abstract
Small-scale farmers often lack access to the expensive agronomic consultants and data analytics suites available to industrial operations. **FarmWise AI** bridges this gap by providing an intelligent, decoupled decision support system. The platform utilizes a multi-agent architecture consisting of a **Random Forest** suitability engine, a **Convolutional Neural Network (CNN)** for disease diagnosis, and a **Hybrid Time-Series** model for market forecasting. By combining expert agronomic rules with machine learning, the system provides "grounded" AI advice that is both statistically accurate and biologically sound.

---

### 2. Introduction & Problem Statement
The "Digital Divide" in agriculture is widening. Modern Ag-Tech is predominantly designed for large-scale monocultures. Small-scale family farms require highly localized advice that accounts for diverse crop rotations and varying soil qualities. 

FarmWise AI addresses three critical uncertainties:
1.  **Selection Risk**: What to plant given current climate trends?
2.  **Economic Risk**: When to sell to maximize profit?
3.  **Pathological Risk**: How to treat crop diseases before they spread?

---

### 3. System Architecture
We adopted a **Decoupled SaaS Architecture** to solve the high-compute requirements of AI models in a web environment.

-   **Frontend (React/TypeScript)**: Hosted on **Vercel** for optimal client-side performance and global delivery.
-   **Backend (FastAPI/Python)**: Hosted on **Render.com**. We moved the "Brain" to a dedicated persistent server to handle high-memory TensorFlow and Scikit-learn workloads that frequently exceeded serverless memory limits (512MB).
-   **Communication**: API requests are transparently routed via a Vercel Proxy, abstracting the multi-cloud setup from the end-user.

---

### 4. AI Technical Deep-Dive

#### 4.1 Agent 1: The Crop Suitability Engine
*   **Model**: **Random Forest Classifier (RFC)**.
*   **Methodology**: We utilized an ensemble of decision trees to predict crop suitability from 8 environmental features (N, P, K, Temp, Humidity, pH, Rainfall).
*   **Hybrid Logic**: To mitigate dataset bias (where the model disproportionately favored specific crops like Soybean), we implemented a **Heuristic Fallback Layer**. The final score is a weighted blend:
    *   **35% ML Probability**: Based on statistical patterns in the historical training data.
    *   **65% Expert Rules**: Based on biological "Safe Bands" for each crop.
*   **Outcome**: This ensures that even if the ML model is uncertain, the system will never recommend a crop that cannot physically survive in the current environment.

#### 4.2 Agent 2: Market Intelligence
*   **Model**: **Random Forest Regression** + **Seasonal Heuristic Multipliers**.
*   **Methodology**: For primary commodities (Corn/Maize), the agent uses a Regression model trained on historical USDA pricing. For other crops, it applies a **Cosine-based Seasonal Model** that correlates price fluctuations with global harvest cycles.
*   **Output**: Identifies "Peak Selling Windows" with confidence levels.

#### 4.3 Agent 3: Crop Health & Diagnosis
*   **Model**: **MobileNetV2 (CNN)**.
*   **Methodology**: We utilized a pre-trained MobileNetV2 architecture fine-tuned on the PlantVillage dataset (38 disease classes).
*   **Engineering Win**: Implemented **Contextual Hinting**. The UI passes the farmer's selected crop type as a metadata hint, which the backend uses to filter and prioritize specific disease classes, significantly reducing "false positives" in visual diagnosis.

---

### 5. Engineering Challenges & Solutions

**Challenge: Cold-Start & Memory Overflows**  
Initial attempts to run TensorFlow models in serverless environments resulted in frequent "Out of Memory" crashes.  
**Solution**: We migrated the backend to a persistent Render environment with 512MB+ dedicated RAM and implemented an asynchronous FastAPI entry point to handle concurrent AI inference tasks without blocking the main event loop.

**Challenge: Model Bias**  
The Suitability ML model showed a 15% bias towards Soybeans due to dataset imbalance.  
**Solution**: We implemented **Penalty Heuristics** that automatically down-weight crops hitting critical environmental mismatches (e.g., Temperature < 15°C for heat-loving crops), regardless of the ML prediction.

---

### 6. Results & Discussion
FarmWise AI successfully provides a unified dashboard that abstracts complex data science into actionable agrarian intelligence. 
*   **Accuracy**: The hybrid suitability engine consistently ranks biologically viable crops higher than pure ML models.
*   **Speed**: MobileNetV2 allows for sub-500ms disease diagnosis, ideal for rural mobile connectivity.
*   **Stability**: The Decoupled Architecture achieved 99.9% uptime during testing, solving the instability of original prototype versions.

---

### 7. Conclusion
FarmWise AI proves that "Small Data" can produce "Big Impact." By combining modern deep learning with traditional agronomic expertise, we created a system that is resilient, affordable, and accurate. Future work will focus on integrating real-time IoT soil sensors directly into the Agent analysis pipeline.

---
*End of Report*
