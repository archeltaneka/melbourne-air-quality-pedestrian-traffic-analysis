document.addEventListener("DOMContentLoaded", function () {
  // Navigation elements
  const navProject = document.getElementById("nav-project");
  const navPollutants = document.getElementById("nav-pollutants");
  const navInteraction = document.getElementById("nav-interaction");

  // Section elements
  const projectInfo = document.getElementById("project-info");
  const visualizationContainer = document.getElementById("visualization-container");
  const mapRadarContainer = document.getElementById("map-radar-container");

  // Control elements
  const timeGranularityDropdown = document.getElementById("time-granularity");
  const startDateInput = document.getElementById("start-date");
  const endDateInput = document.getElementById("end-date");
  const slider = document.getElementById("timeline-slider");
  const sliderValue = document.getElementById("slider-value");

  // Data variables
  let data = null;
  let mapData = null;
  let pollutantData = null;
  let sliderInterval = null;
  let map = null;
  let currentSection = 'project';

  // Create tooltip
  const tooltip = d3.select("body").append("div")
    .attr("class", "tooltip")
    .style("position", "absolute")
    .style("opacity", 0);

  // Navigation functions
  function showSection(sectionName) {
    // Hide all sections
    document.querySelectorAll('.section').forEach(section => {
      section.classList.remove('visible');
      section.style.display = 'none'; // ADD THIS
    });

    // Remove active class from all nav buttons
    document.querySelectorAll('.nav-btn').forEach(btn => {
      btn.classList.remove('active');
    });

    // Show selected section and activate corresponding nav button
    switch (sectionName) {
      case 'project':
        projectInfo.classList.add('visible');
        projectInfo.style.display = 'block'; // ADD THIS
        navProject.classList.add('active');
        currentSection = 'project';
        break;
      case 'pollutants':
        visualizationContainer.classList.add('visible');
        visualizationContainer.style.display = 'block'; // ADD THIS
        navPollutants.classList.add('active');
        currentSection = 'pollutants';
        if (!data) loadData();
        break;
      case 'interaction':
        mapRadarContainer.classList.add('visible');
        mapRadarContainer.style.display = 'block'; // ADD THIS
        navInteraction.classList.add('active');
        currentSection = 'interaction';
        if (!mapData) loadMapData();
        break;
    }

    // Adjust body height to match visible section
    document.body.style.minHeight = 'auto'; // ADD THIS
  }

  // Load air quality data
  async function loadData() {
    try {
      const response = await fetch("../../data/air_quality/air_quality_final.csv");
      const csvData = await response.text();
      data = d3.csvParse(csvData, d => ({
        datetime_AEST: new Date(d.datetime_AEST),
        CO: +d.CO,
        NO2: +d.NO2,
        O3: +d.O3,
        "PM2.5": +d["PM2.5"],
        PM10: +d.PM10
      }));

      // Set default date range
      const minDate = d3.min(data, d => d.datetime_AEST);
      const maxDate = d3.max(data, d => d.datetime_AEST);

      startDateInput.value = formatDate(minDate);
      endDateInput.value = formatDate(maxDate);

      renderPlots("monthly"); // Default to monthly granularity
    } catch (error) {
      console.error("Error loading air quality data:", error);
    }
  }

  // Load pedestrian count data
  async function loadMapData() {
    try {
      const response = await fetch("../../data/pedestrian/pedestrian_count_final.csv");
      const csvData = await response.text();
      mapData = d3.csvParse(csvData, d => ({
        datetime_AEST: new Date(d.datetime_AEST),
        latitude: +d.latitude,
        longitude: +d.longitude,
        area_name: d.area,
        pedestrian_count: +d.pedestrian_count,
        CO: +d.CO,
        NO2: +d.NO2,
        O3: +d.O3,
        "PM2.5": +d["PM2.5"],
        PM10: +d.PM10
      }));

      const minDate = d3.min(mapData, d => d.datetime_AEST);
      const maxDate = d3.max(mapData, d => d.datetime_AEST);

      // Initialize the map and render the initial data
      initializeMapAndRender(mapData.filter(d => d.datetime_AEST.toDateString() === minDate.toDateString()));

      // Initialize filters (slider and date filter)
      initializeSlider(minDate, maxDate);
      initializeDateInputs();

      const startDateFilter = document.getElementById("start-date-filter");
      const endDateFilter = document.getElementById("end-date-filter");

      startDateFilter.value = formatDate(minDate);
      endDateFilter.value = formatDate(maxDate);

      // Create density chart
      createDensityChart();
    } catch (error) {
      console.error("Error loading pedestrian data:", error);
    }
  }

  // Initialize map
  function initializeMap() {
    const map = L.map("map").setView([-37.8136, 144.9631], 14); // Melbourne CBD
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      maxZoom: 18,
    }).addTo(map);
    return map;
  }

  // Add symbols to the map
  function addSymbolsToMap(map, data) {
    data.forEach(d => {
      const { latitude, longitude, pedestrian_count, area_name } = d;
      const radius = Math.sqrt(pedestrian_count) * 0.5; // Scale radius for better visualization

      L.circleMarker([latitude, longitude], {
        radius: Math.max(3, Math.min(15, radius)), // Constrain radius between 3 and 15
        fillColor: "#3182bd",
        color: "#08519c",
        weight: 2,
        opacity: 0.8,
        fillOpacity: 0.6,
      })
        .addTo(map)
        .bindTooltip(
          `<div style="text-align: center; font-family: Arial, sans-serif;">
             <span style="font-size: 16px; font-weight: bold; color: #08519c;">📊 ${Math.floor(pedestrian_count)} pedestrians</span><br>
             <span style="font-size: 14px; color: #333;">📍 ${area_name}</span><br>
             <span style="font-size: 12px; color: #666;">Click for details</span>
           </div>`,
          {
            sticky: true,
            className: 'custom-tooltip'
          }
        );
    });
  }

  // Create density chart
  function createDensityChart() {
    const container = d3.select("#density-chart");
    container.selectAll("*").remove();

    const margin = { top: 20, right: 30, bottom: 60, left: 80 };
    const width = 800 - margin.left - margin.right;
    const height = 400 - margin.top - margin.bottom;

    const svg = container.append("svg")
      .attr("width", width + margin.left + margin.right)
      .attr("height", height + margin.top + margin.bottom)
      .append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);

    // Aggregate data by location and time
    const aggregatedData = d3.groups(mapData, d => d.area_name)
      .map(([area, values]) => {
        const avgPedestrians = d3.mean(values, d => d.pedestrian_count);
        const avgPollutants = {
          CO: d3.mean(values, d => d.CO),
          NO2: d3.mean(values, d => d.NO2),
          O3: d3.mean(values, d => d.O3),
          "PM2.5": d3.mean(values, d => d["PM2.5"]),
          PM10: d3.mean(values, d => d.PM10)
        };

        // Use PM2.5 as representative pollutant
        return {
          area,
          avgPedestrians,
          avgPollutant: avgPollutants["PM2.5"]
        };
      })
      .filter(d => !isNaN(d.avgPollutant) && d.avgPollutant > 0);

    // Create scales
    const xScale = d3.scaleLinear()
      .domain([0, d3.max(aggregatedData, d => d.avgPedestrians)])
      .nice()
      .range([0, width]);

    const yScale = d3.scaleLinear()
      .domain([0, d3.max(aggregatedData, d => d.avgPollutant)])
      .nice()
      .range([height, 0]);

    // Add axes
    svg.append("g")
      .attr("transform", `translate(0,${height})`)
      .call(d3.axisBottom(xScale).tickFormat(d => Math.round(d)))
      .append("text")
      .attr("x", width / 2)
      .attr("y", 40)
      .attr("fill", "#283618")
      .style("text-anchor", "middle")
      .style("font-weight", "bold")
      .text("Average Pedestrian Count");

    svg.append("g")
      .call(d3.axisLeft(yScale).tickFormat(d => d.toFixed(1)))
      .append("text")
      .attr("transform", "rotate(-90)")
      .attr("y", -60)
      .attr("x", -height / 2)
      .attr("fill", "#283618")
      .style("text-anchor", "middle")
      .style("font-weight", "bold")
      .text("PM₂.₅ Concentration (μg/m³)");

    // Add scatter plot
    svg.selectAll("circle")
      .data(aggregatedData)
      .enter().append("circle")
      .attr("cx", d => xScale(d.avgPedestrians))
      .attr("cy", d => yScale(d.avgPollutant))
      .attr("r", 6)
      .attr("fill", "#606c38")
      .attr("opacity", 0.7)
      .attr("stroke", "#283618")
      .attr("stroke-width", 1)
      .on("mouseover", function (event, d) {
        d3.select(this)
          .transition()
          .duration(200)
          .attr("r", 8)
          .attr("fill", "#dda15e");

        tooltip.transition().duration(200).style("opacity", 0.9);
        tooltip.html(`
          <strong>${d.area}</strong><br/>
          Avg Pedestrians: ${Math.round(d.avgPedestrians)}<br/>
          PM₂.₅: ${d.avgPollutant.toFixed(2)} μg/m³
        `)
          .style("left", (event.pageX + 10) + "px")
          .style("top", (event.pageY - 28) + "px");
      })
      .on("mouseout", function () {
        d3.select(this)
          .transition()
          .duration(200)
          .attr("r", 6)
          .attr("fill", "#606c38");

        tooltip.transition().duration(500).style("opacity", 0);
      });

    // Add trend line
    const trendData = d3.regressionLinear()(aggregatedData.map(d => [d.avgPedestrians, d.avgPollutant]));

    svg.append("line")
      .attr("x1", xScale(trendData[0][0]))
      .attr("y1", yScale(trendData[0][1]))
      .attr("x2", xScale(trendData[1][0]))
      .attr("y2", yScale(trendData[1][1]))
      .attr("stroke", "#d7191c")
      .attr("stroke-width", 2)
      .attr("stroke-dasharray", "5,5");
  }

  // Render bar plots based on the selected granularity and date range
  function renderPlots(granularity) {
    // Clear existing plots
    d3.selectAll(".plot").selectAll("*").remove();
    d3.selectAll(".plot-centered").selectAll("*").remove();

    // Get the selected date range
    const startDate = new Date(startDateInput.value);
    const endDate = new Date(endDateInput.value);

    // Filter data based on the selected date range
    const filteredData = data.filter(d => d.datetime_AEST >= startDate && d.datetime_AEST <= endDate);

    // Define time formatting functions for each granularity
    const timeFormat = {
      monthly: d3.timeFormat("%b"),
      daily: d3.timeFormat("%a"),
      hourly: d3.timeFormat("%H:%00")
    };

    // Group data by the selected granularity
    const groupedData = d3.groups(
      filteredData,
      d => {
        switch (granularity) {
          case "monthly":
            return d.datetime_AEST.getMonth();
          case "daily":
            return d.datetime_AEST.getDay();
          case "hourly":
            return d.datetime_AEST.getHours();
          default:
            return d.datetime_AEST.getMonth();
        }
      }
    );

    // Compute average values for each group
    const aggregatedData = groupedData.map(([key, values]) => ({
      key: key,
      CO: d3.mean(values, d => d.CO),
      NO2: d3.mean(values, d => d.NO2),
      O3: d3.mean(values, d => d.O3),
      "PM2.5": d3.mean(values, d => d["PM2.5"]),
      PM10: d3.mean(values, d => d.PM10)
    }));

    // Sort the data properly
    switch (granularity) {
      case "monthly":
        aggregatedData.sort((a, b) => a.key - b.key);
        break;
      case "daily":
        const dayOrder = [1, 2, 3, 4, 5, 6, 0]; // Monday to Sunday
        aggregatedData.sort((a, b) => dayOrder.indexOf(a.key) - dayOrder.indexOf(b.key));
        break;
      case "hourly":
        aggregatedData.sort((a, b) => a.key - b.key);
        break;
    }

    // Create a bar plot for each pollutant
    createBarPlot("#plot-co", aggregatedData, "CO", timeFormat[granularity], granularity, "ppm");
    createBarPlot("#plot-no2", aggregatedData, "NO2", timeFormat[granularity], granularity, "ppb");
    createBarPlot("#plot-o3", aggregatedData, "O3", timeFormat[granularity], granularity, "ppb");
    createBarPlot("#plot-pm25", aggregatedData, "PM2.5", timeFormat[granularity], granularity, "μg/m³");
    createBarPlot("#plot-pm10", aggregatedData, "PM10", timeFormat[granularity], granularity, "μg/m³");
  }

  // Create a bar plot
  function createBarPlot(selector, data, pollutant, timeFormat, granularity, unit) {
    const container = d3.select(selector);
    container.selectAll("*").remove();

    const margin = { top: 40, right: 30, bottom: 60, left: 70 };
    const width = 400 - margin.left - margin.right;
    const height = 300 - margin.top - margin.bottom;

    const svg = container.append("svg")
      .attr("width", width + margin.left + margin.right)
      .attr("height", height + margin.top + margin.bottom)
      .append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);

    // Set X scales
    const xScale = d3.scaleBand()
      .domain(data.map(d => {
        if (granularity === "daily") {
          return ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"][d.key];
        } else if (granularity === "hourly") {
          return d.key.toString().padStart(2, "0") + ":00";
        } else if (granularity === "monthly") {
          return ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][d.key];
        }
        return d.key;
      }))
      .range([0, width])
      .padding(0.2);

    // Set Y scales
    const yScale = d3.scaleLinear()
      .domain([0, d3.max(data, d => d[pollutant]) * 1.1])
      .nice()
      .range([height, 0]);

    // Add X axis
    svg.append("g")
      .attr("transform", `translate(0,${height})`)
      .call(d3.axisBottom(xScale))
      .selectAll("text")
      .style("font-size", "11px")
      .attr("transform", "rotate(-45)")
      .style("text-anchor", "end");

    // Add Y axis
    svg.append("g")
      .call(d3.axisLeft(yScale).tickFormat(d => d.toFixed(2)))
      .selectAll("text")
      .style("font-size", "11px");

    // Add Y axis title
    svg.append("text")
      .attr("transform", "rotate(-90)")
      .attr("y", -50)
      .attr("x", -height / 2)
      .attr("text-anchor", "middle")
      .style("font-size", "12px")
      .style("font-weight", "bold")
      .text(`${pollutant} (${unit})`);

    // Barplot sequential color scale
    const colorScale = d3.scaleSequential()
      .domain([d3.max(data, d => d[pollutant]), 0])
      .interpolator(d3.interpolateRgbBasis(["#d7191c", "#fdae61", "#a6d96a"]));

    // Add bars with animation
    const bars = svg.selectAll("rect")
      .data(data)
      .enter()
      .append("rect")
      .attr("x", d => xScale(granularity === "daily" ? ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"][d.key] :
        granularity === "hourly" ? d.key.toString().padStart(2, "0") + ":00" :
          granularity === "monthly" ? ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][d.key] : d.key))
      .attr("y", height)
      .attr("width", xScale.bandwidth())
      .attr("height", 0)
      .attr("fill", d => colorScale(d[pollutant]))
      .attr("stroke", "#283618")
      .attr("stroke-width", 1);

    // Add transition for animation
    bars.transition()
      .duration(800)
      .delay((d, i) => i * 50)
      .attr("y", d => yScale(d[pollutant]))
      .attr("height", d => height - yScale(d[pollutant]));

    // Add title for each subplot
    svg.append("text")
      .attr("x", width / 2)
      .attr("y", -20)
      .attr("text-anchor", "middle")
      .style("font-size", "16px")
      .style("font-weight", "bold")
      .style("letter-spacing", "0.5px")
      .text(`${pollutant} LEVELS`);

    // Mouse interaction
    bars.on("mouseover", function (event, d) {
      const key = granularity === "daily" ? ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"][d.key] :
        granularity === "hourly" ? d.key.toString().padStart(2, "0") + ":00" :
          granularity === "monthly" ? ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][d.key] : d.key;

      // Highlight this bar
      d3.select(this)
        .transition()
        .duration(200)
        .attr("fill", "#dda15e")
        .attr("stroke-width", 2);

      // Show tooltip
      tooltip.transition().duration(200).style("opacity", 0.9);
      tooltip.html(`
        <strong>Time: ${key}</strong><br/>
        ${pollutant}: ${d[pollutant].toFixed(3)} ${unit}<br/>
        <small>Click to highlight across all charts</small>
      `)
        .style("left", (event.pageX + 10) + "px")
        .style("top", (event.pageY - 28) + "px");
    })
      .on("mouseout", function () {
        // Restore original color
        d3.select(this)
          .transition()
          .duration(200)
          .attr("fill", d => colorScale(d[pollutant]))
          .attr("stroke-width", 1);

        tooltip.transition().duration(500).style("opacity", 0);
      })
      .on("click", function (event, d) {
        // Highlight corresponding bars across all plots
        const key = granularity === "daily" ? ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"][d.key] :
          granularity === "hourly" ? d.key.toString().padStart(2, "0") + ":00" :
            granularity === "monthly" ? ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][d.key] : d.key;

        // Dim all bars
        d3.selectAll(".plot rect, .plot-centered rect")
          .style("opacity", 0.3);

        // Highlight matching bars
        d3.selectAll(".plot rect, .plot-centered rect")
          .filter(function () {
            const barData = d3.select(this).datum();
            if (!barData) return false;

            const barKey = granularity === "daily" ? ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"][barData.key] :
              granularity === "hourly" ? barData.key.toString().padStart(2, "0") + ":00" :
                granularity === "monthly" ? ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][barData.key] : barData.key;

            return barKey === key;
          })
          .style("opacity", 1)
          .attr("fill", "#dda15e");

        // Reset after 3 seconds
        setTimeout(() => {
          d3.selectAll(".plot rect, .plot-centered rect")
            .style("opacity", 1)
            .attr("fill", d => colorScale(d[pollutant]));
        }, 3000);
      });
  }

  // Initialize the map and render the initial data
  function initializeMapAndRender(data) {
    if (map) {
      map.remove();
    }
    map = initializeMap();
    addSymbolsToMap(map, data);
  }

  // Draw radar chart
  function drawRadarChart(data) {
    const radarChartContainer = document.getElementById("radar-chart");
    const containerWidth = radarChartContainer.clientWidth;
    const containerHeight = radarChartContainer.clientHeight;

    const margin = { top: 40, right: 40, bottom: 40, left: 40 };
    const width = containerWidth - margin.left - margin.right;
    const height = containerHeight - margin.top - margin.bottom;

    // Clear existing radar chart
    d3.select("#radar-chart").selectAll("*").remove();

    const svg = d3.select("#radar-chart")
      .append("svg")
      .attr("width", containerWidth)
      .attr("height", containerHeight)
      .append("g")
      .attr("transform", `translate(${margin.left + width / 2}, ${margin.top + height / 2})`);

    const radius = Math.min(width, height) / 2.4;
    const pollutants = ["CO", "NO2", "O3", "PM2.5", "PM10"];

    // Filter out any pollutants with no data
    const radarData = pollutants
      .map(pollutant => ({
        axis: pollutant,
        value: data[pollutant] || 0
      }))
      .filter(d => d.value > 0);

    if (radarData.length === 0) return;

    // Create scale for radar chart axes
    const angleScale = d3.scalePoint()
      .domain(radarData.map(d => d.axis))
      .range([0, 2 * Math.PI])
      .padding(0.1);

    // Create scale for radar chart values
    const maxValue = d3.max(radarData, d => d.value);
    const valueScale = d3.scaleLinear()
      .domain([0, maxValue])
      .range([0, radius]);

    // Draw radar chart axes
    radarData.forEach((d, i) => {
      const angle = angleScale(d.axis);
      const x = Math.cos(angle) * radius;
      const y = Math.sin(angle) * radius;

      // Draw axis line
      svg.append("line")
        .attr("x1", 0)
        .attr("y1", 0)
        .attr("x2", x)
        .attr("y2", y)
        .attr("stroke", "#bc6c25")
        .attr("stroke-width", 1);

      // Add axis label
      svg.append("text")
        .attr("x", x * 1.1)
        .attr("y", y * 1.1)
        .attr("text-anchor", x > 0 ? "start" : "end")
        .attr("dominant-baseline", "middle")
        .style("font-size", "12px")
        .style("font-weight", "bold")
        .text(d.axis);
    });

    // Draw radar chart grid lines
    const levels = 5;
    for (let level = 1; level <= levels; level++) {
      const radiusLevel = (radius / levels) * level;
      svg.append("circle")
        .attr("cx", 0)
        .attr("cy", 0)
        .attr("r", radiusLevel)
        .attr("fill", "none")
        .attr("stroke", "#bc6c25")
        .attr("stroke-dasharray", "2,2")
        .attr("opacity", 0.5);

      // Add value labels
      svg.append("text")
        .attr("x", 5)
        .attr("y", -radiusLevel)
        .style("font-size", "10px")
        .text((maxValue * level / levels).toFixed(1));
    }

    // Draw radar chart polygon
    const line = d3.lineRadial()
      .angle(d => angleScale(d.axis))
      .radius(d => valueScale(d.value))
      .curve(d3.curveLinearClosed);

    svg.append("path")
      .datum(radarData)
      .attr("d", line)
      .attr("fill", "rgba(96, 108, 56, 0.3)")
      .attr("stroke", "#606c38")
      .attr("stroke-width", 3);

    // Add points for each pollutant
    svg.selectAll(".radar-point")
      .data(radarData)
      .enter()
      .append("circle")
      .attr("class", "radar-point")
      .attr("cx", d => Math.cos(angleScale(d.axis)) * valueScale(d.value))
      .attr("cy", d => Math.sin(angleScale(d.axis)) * valueScale(d.value))
      .attr("r", 5)
      .attr("fill", "#283618")
      .attr("stroke", "white")
      .attr("stroke-width", 2)
      .on("mouseover", function (event, d) {
        d3.select(this)
          .transition()
          .duration(200)
          .attr("r", 7)
          .attr("fill", "#dda15e");

        tooltip.transition().duration(200).style("opacity", 0.9);
        tooltip.html(`
          <strong>${d.axis}</strong><br/>
          Concentration: ${d.value.toFixed(3)}<br/>
          Max Value: ${maxValue.toFixed(3)}
        `)
          .style("left", (event.pageX + 10) + "px")
          .style("top", (event.pageY - 28) + "px");
      })
      .on("mouseout", function () {
        d3.select(this)
          .transition()
          .duration(200)
          .attr("r", 5)
          .attr("fill", "#283618");

        tooltip.transition().duration(500).style("opacity", 0);
      });

    // Add title
    svg.append("text")
      .attr("x", 0)
      .attr("y", -radius - 30)
      .attr("text-anchor", "middle")
      .style("font-size", "18px")
      .style("font-weight", "bold")
      .style("letter-spacing", "0.5px")
      .text("POLLUTANT LEVELS");
  }

  // Initialize the slider
  function initializeSlider(minDate, maxDate) {
    const slider = document.getElementById("timeline-slider");
    const sliderValue = document.getElementById("slider-value");

    slider.min = minDate.getTime();
    slider.max = maxDate.getTime();
    slider.step = 60 * 60 * 1000; // 1 hour steps

    slider.value = minDate.getTime();
    sliderValue.textContent = `Date: ${formatDateTime(minDate)}`;
    updateMapAndRadarChart(minDate);
  }

  // Update map and radar chart based on slider
  function updateMapAndRadarChart(selectedDate) {
    if (!map || !mapData) return;

    // Clear existing layers from the map
    map.eachLayer(layer => {
      if (!(layer instanceof L.TileLayer)) {
        map.removeLayer(layer);
      }
    });

    // Filter data for the selected date and hour
    const filteredData = mapData.filter(d => {
      return (
        d.datetime_AEST.toDateString() === selectedDate.toDateString() &&
        d.datetime_AEST.getHours() === selectedDate.getHours()
      );
    });

    // Re-render the map with filtered data
    addSymbolsToMap(map, filteredData);

    // Compute average pollutant levels for the radar chart
    pollutantData = data.filter(d => {
      return (
        d.datetime_AEST.toDateString() === selectedDate.toDateString() &&
        d.datetime_AEST.getHours() === selectedDate.getHours()
      );
    });

    const aggregatedData = {
      CO: d3.mean(pollutantData, d => d.CO) || 0,
      NO2: d3.mean(pollutantData, d => d.NO2) || 0,
      O3: d3.mean(pollutantData, d => d.O3) || 0,
      "PM2.5": d3.mean(pollutantData, d => d["PM2.5"]) || 0,
      PM10: d3.mean(pollutantData, d => d.PM10) || 0
    };

    // Update the radar chart
    drawRadarChart(aggregatedData);
  }

  // Initialize Start Date and End Date inputs
  function initializeDateInputs() {
    const minDate = d3.min(mapData, d => d.datetime_AEST);
    const maxDate = d3.max(mapData, d => d.datetime_AEST);

    document.getElementById("start-date").value = formatDate(minDate);
    document.getElementById("end-date").value = formatDate(maxDate);
    document.getElementById("start-date-filter").value = formatDate(minDate);
    document.getElementById("end-date-filter").value = formatDate(maxDate);
  }

  // Play slider after clicking "Play" button
  function playSlider() {
    if (sliderInterval) return;

    const slider = document.getElementById("timeline-slider");
    const sliderValue = document.getElementById("slider-value");
    const step = 60 * 60 * 1000; // 1 hour

    sliderInterval = setInterval(() => {
      const currentValue = parseInt(slider.value);
      const maxValue = parseInt(slider.max);

      if (currentValue + step <= maxValue) {
        slider.value = currentValue + step;
        const newDate = new Date(parseInt(slider.value));
        sliderValue.textContent = `Date: ${formatDateTime(newDate)}`;
        updateMapAndRadarChart(newDate);
      } else {
        stopSlider();
      }
    }, 1000);
  }

  // Stop button
  function stopSlider() {
    if (sliderInterval) {
      clearInterval(sliderInterval);
      sliderInterval = null;
    }
  }

  // Reset button
  function resetSlider() {
    stopSlider();

    const slider = document.getElementById("timeline-slider");
    const sliderValue = document.getElementById("slider-value");
    const startDateFilter = document.getElementById("start-date-filter");
    const endDateFilter = document.getElementById("end-date-filter");

    if (mapData) {
      const minDate = d3.min(mapData, d => d.datetime_AEST);
      const maxDate = d3.max(mapData, d => d.datetime_AEST);

      slider.min = minDate.getTime();
      slider.max = maxDate.getTime();
      slider.value = minDate.getTime();

      startDateFilter.value = formatDate(minDate);
      endDateFilter.value = formatDate(maxDate);

      sliderValue.textContent = `Date: ${formatDateTime(minDate)}`;
      updateMapAndRadarChart(minDate);
    }
  }

  // Next button
  function nextSlider() {
    const slider = document.getElementById("timeline-slider");
    const sliderValue = document.getElementById("slider-value");
    const currentValue = parseInt(slider.value);
    const maxValue = parseInt(slider.max);
    const step = 60 * 60 * 1000; // 1 hour

    if (currentValue + step <= maxValue) {
      slider.value = currentValue + step;
      const newDate = new Date(parseInt(slider.value));
      sliderValue.textContent = `Date: ${formatDateTime(newDate)}`;
      updateMapAndRadarChart(newDate);
    }
  }

  // Prev button
  function prevSlider() {
    const slider = document.getElementById("timeline-slider");
    const sliderValue = document.getElementById("slider-value");
    const currentValue = parseInt(slider.value);
    const minValue = parseInt(slider.min);
    const step = 60 * 60 * 1000; // 1 hour

    if (currentValue - step >= minValue) {
      slider.value = currentValue - step;
      const newDate = new Date(parseInt(slider.value));
      sliderValue.textContent = `Date: ${formatDateTime(newDate)}`;
      updateMapAndRadarChart(newDate);
    }
  }

  // Helper function to format date and time
  function formatDateTime(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");
    const hour = String(date.getHours()).padStart(2, "0");
    return `${year}-${month}-${day} ${hour}:00`;
  }

  // Helper function to format dates for input fields
  function formatDate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");
    return `${year}-${month}-${day}`;
  }

  // Event listeners for navigation
  navProject.addEventListener("click", () => showSection('project'));
  navPollutants.addEventListener("click", () => showSection('pollutants'));
  navInteraction.addEventListener("click", () => showSection('interaction'));

  // Event listeners for controls
  timeGranularityDropdown.addEventListener("change", () => {
    renderPlots(timeGranularityDropdown.value);
  });

  startDateInput.addEventListener("change", () => {
    renderPlots(timeGranularityDropdown.value);
  });

  endDateInput.addEventListener("change", () => {
    renderPlots(timeGranularityDropdown.value);
  });

  // Slider event listeners
  slider.addEventListener("input", function () {
    const selectedDate = new Date(parseInt(this.value));
    sliderValue.textContent = `Date: ${formatDateTime(selectedDate)}`;
    updateMapAndRadarChart(selectedDate);
  });

  // Button event listeners
  document.getElementById("play-button").addEventListener("click", playSlider);
  document.getElementById("stop-button").addEventListener("click", stopSlider);
  document.getElementById("reset-button").addEventListener("click", resetSlider);
  document.getElementById("next-button").addEventListener("click", nextSlider);
  document.getElementById("prev-button").addEventListener("click", prevSlider);

  // Date filter event listeners
  document.getElementById("start-date-filter").addEventListener("change", function () {
    const slider = document.getElementById("timeline-slider");
    const newStartDate = new Date(this.value + "T00:00:00");
    slider.min = newStartDate.getTime();

    if (parseInt(slider.value) < slider.min) {
      slider.value = slider.min;
      const newDate = new Date(parseInt(slider.value));
      sliderValue.textContent = `Date: ${formatDateTime(newDate)}`;
      updateMapAndRadarChart(newDate);
    }
  });

  document.getElementById("end-date-filter").addEventListener("change", function () {
    const slider = document.getElementById("timeline-slider");
    const newEndDate = new Date(this.value + "T23:00:00");
    slider.max = newEndDate.getTime();

    if (parseInt(slider.value) > slider.max) {
      slider.value = slider.max;
      const newDate = new Date(parseInt(slider.value));
      sliderValue.textContent = `Date: ${formatDateTime(newDate)}`;
      updateMapAndRadarChart(newDate);
    }
  });

  // Initialize with project section visible
  showSection('project');
});