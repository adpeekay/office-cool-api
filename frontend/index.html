<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>Cooling & Glazing Comparison</title>

  <!-- Chart.js -->
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

  <style>
    body {
      font-family: Arial, sans-serif;
      margin: 2rem;
    }

    h2 {
      margin-top: 2rem;
    }

    .container {
      max-width: 900px;
      margin: auto;
    }

    .chart-container {
      margin-top: 2rem;
    }

    table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 1.5rem;
    }

    th, td {
      padding: 0.6rem;
      border-bottom: 1px solid #ddd;
      text-align: left;
    }

    th {
      background: #f5f5f5;
    }

    .note {
      margin-top: 1rem;
      font-size: 0.9rem;
      color: #555;
    }
  </style>
</head>

<body>
  <div class="container">
    <h1>Glazing Cooling Comparison</h1>

    <p>
      Click a location on the map to compare annual cooling burden for
      different glazing options.
    </p>

    <h2>Annual cooling energy</h2>

    <div class="chart-container">
      <canvas id="coolingChart"></canvas>
    </div>

    <h2>Energy, CO₂ and cost savings</h2>

    <table>
      <thead>
        <tr>
          <th>Glazing option</th>
          <th>Cooling energy saved</th>
          <th>CO₂ saved</th>
          <th>Annual cost saving</th>
        </tr>
      </thead>
      <tbody id="savingsBody"></tbody>
    </table>

    <p class="note">
      Cooling results represent a simplified, comparative metric driven by
      façade solar gains and internal loads. They are intended for relative
      comparison of glazing options, not absolute HVAC energy prediction.
    </p>
  </div>

  <script>
    // === UK default assumptions ===
    const GRID_CARBON = 0.18;        // kg CO2 per kWh
    const ELECTRICITY_PRICE = 0.28;  // £ per kWh

    let coolingChart = null;

    // === Call this from your map click handler ===
    async function fetchCoolingComparison(lat, lon) {
      const response = await fetch("https://YOUR-API.onrender.com/cooling", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          lat: lat,
          lon: lon,
          floor_area: 150,
          cooling_setpoint: 24
        })
      });

      const data = await response.json();
      renderCoolingResults(data);
    }

    function renderCoolingResults(data) {
      const labels = ["Normal glass", "Solar control", "CdTe PV"];
      const values = [
        data.results.normal.annual_cooling_kwh,
        data.results.solar_control.annual_cooling_kwh,
        data.results.cdte_pv.annual_cooling_kwh
      ];

      const ctx = document.getElementById("coolingChart").getContext("2d");

      if (coolingChart) {
        coolingChart.destroy();
      }

      coolingChart = new Chart(ctx, {
        type: "bar",
        data: {
          labels: labels,
          datasets: [{
            label: "Annual cooling energy (kWh/year)",
            data: values,
            backgroundColor: ["#999999", "#4da6ff", "#2ecc71"]
          }]
        },
        options: {
          responsive: true,
          scales: {
            y: { beginAtZero: true }
          }
        }
      });

      renderSavingsTable(data);
    }

    function renderSavingsTable(data) {
      const base = data.results.normal.annual_cooling_kwh;

      const scenarios = [
        { name: "Solar control", kwh: data.results.solar_control.annual_cooling_kwh },
        { name: "CdTe PV", kwh: data.results.cdte_pv.annual_cooling_kwh }
      ];

      let html = "";

      scenarios.forEach(s => {
        const delta = base - s.kwh;
        const co2 = delta * GRID_CARBON;
        const cost = delta * ELECTRICITY_PRICE;

        html += `
          <tr>
            <td>${s.name}</td>
            <td>${delta.toFixed(0)} kWh</td>
            <td>${co2.toFixed(0)} kg CO₂</td>
            <td>£${cost.toFixed(0)}</td>
          </tr>
        `;
      });

      document.getElementById("savingsBody").innerHTML = html;
    }

    // === TEMPORARY TEST CALL (remove once wired to map) ===
    // Cambridge example
    fetchCoolingComparison(52.205, 0.1218);
  </script>
</body>
</html>
