document.addEventListener("DOMContentLoaded", function () {
  const projectInfo = document.getElementById("project-info");
  const visualizationContainer = document.getElementById("visualization-container");
  const mapRadarContainer = document.getElementById("map-radar-container");
  const timeGranularityDropdown = document.getElementById("time-granularity");
  const startDateInput = document.getElementById("start-date");
  const endDateInput = document.getElementById("end-date");
  const slider = document.getElementById("timeline-slider");
  const sliderValue = document.getElementById("slider-value");

  let isVisualizationVisible = false;
  let isMapVisible = false;
  let data = null;
  let mapData = null;
  let pollutantData = null;
  let sliderInterval = null;

  const tooltip = d3.select("body").append("div")
    .attr("class", "tooltip")
    .style("position", "absolute")
    .style("background", "#fff")
    .style("padding", "10px")
    .style("border", "1px solid #ccc")
    .style("border-radius", "5px")
    .style("opacity", 0);

  // Reset visibility and transitions
  projectInfo.style.opacity = "1";
  projectInfo.style.transform = "translateY(0)";
  visualizationContainer.classList.remove("visible");
  visualizationContainer.style.opacity = "0";
  visualizationContainer.style.transform = "translateY(20px)";
  mapRadarContainer.style.opacity = "0";
  mapRadarContainer.style.transform = "translateY(20px)";

  // Load air quality data
  async function loadData() {
    const response = await fetch("../web/data/air_quality/air_quality_final.csv");
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
  }

  // Load pedestrian count data
  async function loadMapData() {
    const response = await fetch("../web/data/pedestrian/pedestrian_count_final.csv");
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

    // Filter data for the smallest possible date value initially
    const initialData = mapData.filter(d => d.datetime_AEST.toDateString() === minDate.toDateString());

    // Initialize the map and render the initial data
    initializeMapAndRender(initialData);

    // Initialize filters (slider and date filter)
    initializeSlider(minDate, maxDate);
    initializeDateInputs();

    const startDateFilter = document.getElementById("start-date-filter");
    const endDateFilter = document.getElementById("end-date-filter");

    startDateFilter.value = formatDate(minDate);
    endDateFilter.value = formatDate(maxDate);
  }

  // Initialize map
  function initializeMap() {
    const map = L.map("map").setView([-37.8136, 144.9631], 14); // Set it in the middle of Melbourne CBD
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>  contributors',
      maxZoom: 18,
    }).addTo(map);
    return map;
  }

  // Add symbols to the map, representing number of pedestrians
  function addSymbolsToMap(map, data) {
    data.forEach(d => {
      const { latitude, longitude, pedestrian_count, area_name } = d;
      // Add a circle marker for each data point
      L.circleMarker([latitude, longitude], {
        radius: Math.sqrt(pedestrian_count), // Scale radius based on pedestrian count
        fillColor: "blue",
        color: "#000",
        weight: 1,
        opacity: 0.8,
        fillOpacity: 0.6,
      })
        .addTo(map)
        .bindTooltip(
          `<div style="text-align: center;">
             <span style="font-size: 18px; font-weight: bold;">Number of Pedestrians: ${Math.floor(pedestrian_count)}</span><br>
             <span style="font-size: 12px;">Area: ${area_name}</span>
           </div>`,
          {
            sticky: true, // Keep the tooltip visible while hovering
          }
        );
    });
  }

  // Render barplots based on the selected granularity and date range
  function renderPlots(granularity) {
    // Clear existing plots by removing all child elements
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
      weekly: d3.timeFormat("%U"),
      daily: d3.timeFormat("%a"),
      hourly: d3.timeFormat("%H")
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
      CO: d3.median(values, d => d.CO),
      NO2: d3.median(values, d => d.NO2),
      O3: d3.median(values, d => d.O3),
      "PM2.5": d3.median(values, d => d["PM2.5"]),
      PM10: d3.median(values, d => d.PM10)
    }));

    // Sort the data for "daily" filter
    switch (granularity) {
      case "monthly":
        aggregatedData.sort((a, b) => d3.timeMonth(new Date(`2022-${a.key}-01`)) - d3.timeMonth(new Date(`2022-${b.key}-01`)));
        break;
      case "daily":
        aggregatedData.sort((a, b) => ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].indexOf(a.key) - ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].indexOf(b.key));
        break;
      case "hourly":
        aggregatedData.sort((a, b) => a.key - b.key);
        break;
    }

    // Create a bar plot for each pollutant
    createBarPlot("#plot-co", aggregatedData, "CO", timeFormat[granularity], granularity);
    createBarPlot("#plot-no2", aggregatedData, "NO2", timeFormat[granularity], granularity);
    createBarPlot("#plot-o3", aggregatedData, "O3", timeFormat[granularity], granularity);
    createBarPlot("#plot-pm25", aggregatedData, "PM2.5", timeFormat[granularity], granularity);
    createBarPlot("#plot-pm10", aggregatedData, "PM10", timeFormat[granularity], granularity);
  }

  // Create a bar plot
  function createBarPlot(selector, data, pollutant, timeFormat, granularity) {
    const margin = { top: 20, right: 30, bottom: 40, left: 50 };
    const width = 300 - margin.left - margin.right;
    const height = 200 - margin.top - margin.bottom;

    // Append SVG to the plot container
    const svg = d3.select(selector)
      .append("svg")
      .attr("width", width + margin.left + margin.right)
      .attr("height", height + margin.top + margin.bottom)
      .append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);

    // Set X scales
    const xScale = d3.scaleBand()
      .domain(
        granularity === "daily"
          ? [0, 1, 2, 3, 4, 5, 6]
          : granularity === "hourly"
            ? Array.from({ length: 24 }, (_, i) => i)
            : granularity === "monthly"
              ? Array.from({ length: 12 }, (_, i) => i)
              : data.map(d => timeFormat(d.key))
      )
      .range([0, width])
      .padding(0.2);

    // Set Y scales
    const yScale = d3.scaleLinear()
      .domain([0, d3.max(data, d => d[pollutant])])
      .nice()
      .range([height, 0]);

    // Add X axis
    svg.append("g")
      .attr("transform", `translate(0,${height})`)
      .call(d3.axisBottom(xScale)
        .tickFormat(d => {
          if (granularity === "daily") {
            return ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"][d];
          } else if (granularity === "hourly") {
            return d.toString();
          } else if (granularity === "monthly") {
            return ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][d];
          } else {
            return timeFormat(new Date(d));
          }
        })
      )
      .selectAll("text")
      .style("font-size", "10px")
      .attr("transform", "rotate(-45)")
      .style("text-anchor", "end");

    // Add Y axis
    svg.append("g")
      .call(d3.axisLeft(yScale));

    // Barplot sequential color scale
    const colorScale = d3.scaleSequential()
      .domain([d3.max(data, d => d[pollutant]), 0])
      .interpolator(d3.interpolateRgbBasis(["#d7191c", "#fdae61", "#a6d96a"])); // red-orange-green sequential color for pollutant levels

    // Add bars with animation
    const bars = svg.selectAll("rect")
      .data(data)
      .enter()
      .append("rect")
      .attr("x", d => xScale(granularity === "daily" || granularity === "hourly" || granularity === "monthly" ? d.key : timeFormat(d.key)))
      .attr("y", height)
      .attr("width", xScale.bandwidth())
      .attr("height", 0) // Initial height is 0
      .attr("fill", d => colorScale(d[pollutant]));

    // Add transition for animation
    bars.transition()
      .duration(800)
      .delay((d, i) => i * 50) // Delay each bar's animation slightly
      .attr("y", d => yScale(d[pollutant])) // Animate to the correct height
      .attr("height", d => height - yScale(d[pollutant]));

    // Add title for each subplot
    svg.append("text")
      .attr("x", width / 2)
      .attr("y", -5)
      .attr("text-anchor", "middle")
      .style("font-size", "14px")
      .style("font-weight", "bold")
      .style("letter-spacing", "0.5px") // Add letter spacing
      .text(`${pollutant} LEVELS`);

    // Mouse over event
    bars.on("mouseover", (event, d) => {
      // Determine the hovered key based on granularity
      const hoveredKey = granularity === "daily"
        ? ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"][d.key] // Map numeric key to day name
        : granularity === "hourly"
          ? d.key.toString().padStart(2, "0")
          : granularity === "monthly"
            ? ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][d.key] // Map numeric key to month name
            : timeFormat(d.key);

      // Highlight corresponding bars across all plots
      d3.selectAll(".plot rect, .plot-centered rect")
        .style("opacity", 0.1); // Dim all bars
      d3.selectAll(".plot rect, .plot-centered rect")
        .filter(rectD => {
          const key = granularity === "daily"
            ? ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"][rectD.key]
            : granularity === "hourly"
              ? rectD.key.toString().padStart(2, "0")
              : granularity === "monthly"
                ? ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][rectD.key]
                : timeFormat(rectD.key);
          return key === hoveredKey;
        })
        .style("opacity", 1); // Highlight matching bars

      // Show tooltip
      const hoveredData = data.find(x => {
        const key = granularity === "daily"
          ? ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"][x.key]
          : granularity === "hourly"
            ? x.key.toString().padStart(2, "0")
            : granularity === "monthly"
              ? ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][x.key]
              : timeFormat(x.key);
        return key === hoveredKey;
      });
      if (hoveredData) {
        tooltip.transition().duration(200).style("opacity", 0.9);
        tooltip.html(
          `Time: ${hoveredKey}<br>` +
          `CO: ${formatValue(hoveredData.CO)}<br>` +
          `NO2: ${formatValue(hoveredData.NO2)}<br>` +
          `O3: ${formatValue(hoveredData.O3)}<br>` +
          `PM2.5: ${formatValue(hoveredData["PM2.5"])}<br>` +
          `PM10: ${formatValue(hoveredData.PM10)}`
        )
          .style("left", `${event.pageX + 10}px`)
          .style("top", `${event.pageY - 10}px`);
      }
    });

    // Mouse out event
    bars.on("mouseout", () => {
      // Reset opacity of all bars
      d3.selectAll(".plot rect, .plot-centered rect")
        .style("opacity", 1);

      // Hide tooltip
      tooltip.transition().duration(200).style("opacity", 0);
    });
  }

  // Initialize the map and render the initial data
  function initializeMapAndRender(data) {
    map = initializeMap();
    addSymbolsToMap(map, data);
  }

  // Draw radar chart
  function drawRadarChart(data) {
    const radarChartContainer = document.getElementById("radar-chart");
    const containerWidth = radarChartContainer.clientWidth;
    const containerHeight = radarChartContainer.clientHeight;

    // Define margins
    const margin = { top: 20, right: 20, bottom: 20, left: 50 };
    const width = containerWidth - margin.left - margin.right;
    const height = containerHeight - margin.top - margin.bottom;

    // Clear existing radar chart
    d3.select("#radar-chart").selectAll("*").remove();

    // Append SVG to the radar chart container
    const svg = d3.select("#radar-chart")
      .append("svg")
      .attr("width", containerWidth)
      .attr("height", containerHeight)
      .append("g")
      .attr("transform", `translate(${margin.left + width / 2}, ${margin.top + height / 2})`);

    // Define the radar chart dimensions
    const radius = Math.min(width, height) / 2.4;

    // Define the data format for the radar chart
    const pollutants = ["CO", "NO2", "O3", "PM2.5", "PM10"];
    const radarData = pollutants.map(pollutant => ({
      axis: pollutant,
      value: data[pollutant] || 0 // Use 0 if no data is available
    }));

    // Create scale for radar chart axes
    const angleScale = d3.scalePoint()
      .domain(pollutants)
      .range([0, 2.5 * Math.PI])
      .padding(1); // Add padding to avoid overlap

    // Create scale for radar chart values
    const valueScale = d3.scaleLinear()
      .domain([0, d3.max(radarData, d => d.value)])
      .range([0, radius]);

    // Draw radar chart axes
    pollutants.forEach((pollutant, i) => {
      const angle = angleScale(pollutant);
      const x = Math.cos(angle) * radius;
      const y = Math.sin(angle) * radius;

      // Draw axis line
      svg.append("line")
        .attr("x1", 0)
        .attr("y1", 0)
        .attr("x2", x)
        .attr("y2", y)
        .attr("stroke", "#bc6c25");

      // Add axis label
      svg.append("text")
        .attr("x", x > 0 ? x + 10 : x - 10) // Adjust position based on angle
        .attr("y", y)
        .attr("text-anchor", x > 0 ? "start" : "end")
        .text(pollutant);
    });

    // Draw radar chart grid lines
    for (let level = 1; level <= 5; level++) {
      const radiusLevel = (radius / 5) * level;
      svg.append("circle")
        .attr("cx", 0)
        .attr("cy", 0)
        .attr("r", radiusLevel)
        .attr("fill", "none")
        .attr("stroke", "#bc6c25")
        .attr("stroke-dasharray", "2");
    }

    // Draw radar chart polygon
    const line = d3.lineRadial()
      .angle(d => angleScale(d.axis) + Math.PI / 2) // Use angleScale for angles
      .radius(d => valueScale(d.value)); // Use valueScale for radius

    svg.append("path")
      .datum(radarData)
      .attr("d", line) // Draw the polygon
      .attr("fill", "rgba(96, 108, 56, 0.5)")
      .attr("stroke", "#bc6c25")
      .attr("stroke-width", 2);

    // Add points for each pollutant
    svg.selectAll(".radar-point")
      .data(radarData)
      .enter()
      .append("circle")
      .attr("class", "radar-point")
      .attr("cx", d => Math.cos(angleScale(d.axis)) * valueScale(d.value))
      .attr("cy", d => Math.sin(angleScale(d.axis)) * valueScale(d.value))
      .attr("r", 5)
      .attr("fill", "#283618");

    svg.append("text")
      .attr("x", -5)
      .attr("y", -220)
      .attr("text-anchor", "middle")
      .style("font-size", "22px")
      .text(`POLLUTANT LEVELS`)
      .style("font-weight", "bold")
      .style("letter-spacing", "0.5px"); // Add letter spacing
  }

  // Initialize the slider
  function initializeSlider() {
    const dates = mapData.map(d => d.datetime_AEST);
    const minDate = d3.min(dates);
    const maxDate = d3.max(dates);

    // Set default slider range
    const slider = document.getElementById("timeline-slider");
    const sliderValue = document.getElementById("slider-value");

    slider.min = minDate.getTime();
    slider.max = maxDate.getTime();

    // Initialize calendar filters
    const startDateFilter = document.getElementById("start-date-filter");
    const endDateFilter = document.getElementById("end-date-filter");

    startDateFilter.value = formatDate(minDate); // Default to min date
    endDateFilter.value = formatDate(maxDate); // Default to max date

    // Event listener for Start Date filter
    startDateFilter.addEventListener("change", () => {
      const selectedStartDate = new Date(startDateFilter.value + "T00:00:00"); // Start from to 00:00 AM
      const selectedEndDate = new Date(endDateFilter.value + "T23:00:00"); // Ends on 23:00 PM

      if (selectedStartDate > selectedEndDate) {
        alert("Start Date cannot be later than End Date.");
        return;
      }

      // Update slider min value
      slider.min = selectedStartDate.getTime();
      slider.value = Math.max(+slider.value, +slider.min); // Ensure slider value >= new min

      // Update map and radar chart
      updateMapAndRadarChart(new Date(+slider.value));
      sliderValue.textContent = `Date: ${formatDateTime(new Date(+slider.value))}`;
    });

    // Event listener for End Date filter
    endDateFilter.addEventListener("change", () => {
      const selectedStartDate = new Date(startDateFilter.value + "T00:00:00"); // Set to 00:00 AM
      const selectedEndDate = new Date(endDateFilter.value + "T23:00:00"); // Set to 23:00 PM

      if (selectedStartDate > selectedEndDate) {
        alert("End Date cannot be earlier than Start Date.");
        return;
      }

      // Update slider max value
      slider.max = selectedEndDate.getTime();
      slider.value = Math.min(+slider.value, +slider.max); // Ensure slider value <= new max

      // Update map and radar chart
      updateMapAndRadarChart(new Date(+slider.value));
      sliderValue.textContent = `Date: ${formatDateTime(new Date(+slider.value))}`;
    });

    // Add input event listener for manual slider dragging
    slider.addEventListener("input", () => {
      const selectedDate = new Date(+slider.value);
      sliderValue.textContent = `Date: ${formatDateTime(selectedDate)}`;
      updateMapAndRadarChart(selectedDate);
    });

    // Set default slider value
    slider.value = minDate.getTime();
    sliderValue.textContent = `Date: ${formatDateTime(minDate)}`;
    updateMapAndRadarChart(minDate);
  }

  // Helper function to format date and time
  function formatDateTime(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");
    const hour = String(date.getHours()).padStart(2, "0");
    return `${year}-${month}-${day} ${hour}:00`;
  }

  function updateMapAndRadarChart(selectedDate) {
    if (!map) {
      console.error("Map is not initialized!");
      return;
    }

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
      CO: d3.mean(pollutantData, d => d.CO),
      NO2: d3.mean(pollutantData, d => d.NO2),
      O3: d3.mean(pollutantData, d => d.O3),
      "PM2.5": d3.mean(pollutantData, d => d["PM2.5"]),
      PM10: d3.mean(pollutantData, d => d.PM10)
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
  }

  // Play slider after clicking "Play" button
  function playSlider() {
    if (sliderInterval) return; // Prevent multiple intervals
    const min = +slider.min;
    const max = +slider.max;
    const step = 60 * 60 * 1000; // Increment by one hour (adjust as needed)
    sliderInterval = setInterval(() => {
      const currentValue = +slider.value;
      if (currentValue + step <= max) {
        slider.value = currentValue + step; // Increment slider value
        updateMapAndRadarChart(new Date(+slider.value)); // Update map and radar chart
        sliderValue.textContent = `Date: ${formatDateTime(new Date(+slider.value))}`; // Update slider label
      } else {
        slider.value = max; // Ensure slider stops at the maximum value
        updateMapAndRadarChart(new Date(+slider.value));
        stopSlider(); // Stop when slider reaches the end
      }
    }, 500); // Adjust interval duration (in milliseconds)
  }

  // Stop button
  function stopSlider() {
    if (sliderInterval) {
      clearInterval(sliderInterval); // Clear the interval
      sliderInterval = null; // Reset the interval variable
    }
  }

  // Reset button
  function resetSlider() {
    stopSlider(); // Stop any ongoing play action

    const dates = mapData.map(d => d.datetime_AEST);
    const minDate = d3.min(dates);
    const maxDate = d3.max(dates);

    // Reset slider range
    slider.min = minDate.getTime();
    slider.max = maxDate.getTime();

    // Reset slider value to the minimum
    slider.value = minDate.getTime();

    // Reset calendar filters
    const startDateFilter = document.getElementById("start-date-filter");
    const endDateFilter = document.getElementById("end-date-filter");

    startDateFilter.value = formatDate(minDate);
    endDateFilter.value = formatDate(maxDate);

    // Update map and radar chart
    updateMapAndRadarChart(new Date(+slider.value));

    // Update slider label
    sliderValue.textContent = `Date: ${formatDateTime(new Date(+slider.value))}`;
  }

  // Next button
  function nextSlider() {
    const currentValue = +slider.value;
    const max = +slider.max;
    const oneHourInMs = 3600000; // 1 hour in milliseconds

    if (currentValue + oneHourInMs <= max) {
      slider.value = currentValue + oneHourInMs; // Increment slider value by 1 hour
      updateMapAndRadarChart(new Date(+slider.value)); // Update map and radar chart
      sliderValue.textContent = `Date: ${formatDateTime(new Date(+slider.value))}`; // Update slider label
    }
  }

  // Prev button
  function prevSlider() {
    const currentValue = +slider.value;
    const min = +slider.min;
    const oneHourInMs = 3600000; // 1 hour in milliseconds

    if (currentValue - oneHourInMs >= min) {
      slider.value = currentValue - oneHourInMs; // Decrement slider value by 1 hour
      updateMapAndRadarChart(new Date(+slider.value)); // Update map and radar chart
      sliderValue.textContent = `Date: ${formatDateTime(new Date(+slider.value))}`; // Update slider label
    }
  }

  // Function to update the slider range based on Start Date and End Date
  function updateSliderRange() {
    const startDate = new Date(document.getElementById("start-date").value);
    const endDate = new Date(document.getElementById("end-date").value);

    // Validate the selected dates
    if (isNaN(startDate) || isNaN(endDate)) {
      alert("Please select valid start and end dates.");
      return;
    }

    if (startDate > endDate) {
      alert("Start date must be earlier than or equal to end date.");
      return;
    }

    // Set the slider range
    const minTimestamp = startDate.setHours(0, 0, 0, 0); // Start at 00:00 AM
    const maxTimestamp = endDate.setHours(23, 0, 0, 0); // End at 23:00 PM

    slider.min = minTimestamp;
    slider.max = maxTimestamp;

    // Ensure the current slider value stays within the new range
    if (+slider.value < minTimestamp) {
      slider.value = minTimestamp; // Reset to the new minimum if out of range
    } else if (+slider.value > maxTimestamp) {
      slider.value = maxTimestamp; // Reset to the new maximum if out of range
    }

    // Update the slider label
    sliderValue.textContent = `Date: ${formatDateTime(new Date(+slider.value))}`;

    // Update the map and radar chart
    updateMapAndRadarChart(new Date(+slider.value));
  }

  // Handle scroll events
  function handleScroll() {
    const projectInfoRect = projectInfo.getBoundingClientRect();
    const visualizationRect = visualizationContainer.getBoundingClientRect();
    const mapRect = mapRadarContainer.getBoundingClientRect();

    // Scroll down logic
    if (projectInfoRect.bottom <= window.innerHeight * 0.25 && !isVisualizationVisible) {
      // Fade out project-info and fade in visualization-container
      fadeOut(projectInfo, () => {
        fadeIn(visualizationContainer);
        if (!data) loadData();
        isVisualizationVisible = true;
      });
    }

    if (visualizationRect.bottom <= window.innerHeight * 0.25 && !isMapVisible && isVisualizationVisible) {
      // Fade out visualization-container and fade in map-radar-container
      fadeOut(visualizationContainer, () => {
        fadeIn(mapRadarContainer);
        if (!mapData) loadMapData();
        isMapVisible = true;
      });
    }

    // Scroll up logic
    if (mapRect.top >= window.innerHeight * 0.75 && isMapVisible) {
      // Fade out map-radar-container and fade in visualization-container
      fadeOut(mapRadarContainer, () => {
        fadeIn(visualizationContainer);
        isMapVisible = false;
      });
    }

    if (visualizationRect.top >= window.innerHeight * 0.75 && isVisualizationVisible && !isMapVisible) {
      // Fade out visualization-container and fade in project-info
      fadeOut(visualizationContainer, () => {
        fadeIn(projectInfo);
        isVisualizationVisible = false;
      });
    }
  }

  // Fade out functionality
  function fadeOut(element, callback) {
    element.style.transition = "opacity 1s ease-in-out";
    element.style.opacity = "0";
    setTimeout(() => {
      element.style.visibility = "hidden";
      if (callback) callback();
    }, 300); // Match the duration of the transition
  }

  // Fade in functionality
  function fadeIn(element) {
    element.style.visibility = "visible";
    element.style.transition = "opacity 1s ease-in-out";
    element.style.opacity = "1";
  }

  // Helper function to format dates for input fields
  function formatDate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");
    return `${year}-${month}-${day}`;
  }

  // Helper function to format values
  function formatValue(value) {
    return value.toFixed(3);
  }

  // Add event listeners
  window.addEventListener("scroll", handleScroll);
  timeGranularityDropdown.addEventListener("change", () => renderPlots(timeGranularityDropdown.value));
  startDateInput.addEventListener("change", () => renderPlots(timeGranularityDropdown.value));
  endDateInput.addEventListener("change", () => renderPlots(timeGranularityDropdown.value));
  document.getElementById("play-button").addEventListener("click", playSlider);
  document.getElementById("stop-button").addEventListener("click", stopSlider);
  document.getElementById("reset-button").addEventListener("click", resetSlider);
  document.getElementById("next-button").addEventListener("click", nextSlider);
  document.getElementById("prev-button").addEventListener("click", prevSlider);
  document.getElementById("start-date").addEventListener("input", updateSliderRange);
  document.getElementById("end-date").addEventListener("input", updateSliderRange);

  // Initialize visibility
  projectInfo.style.opacity = "1";
  visualizationContainer.style.opacity = "0";
  visualizationContainer.style.visibility = "hidden";
  mapRadarContainer.style.opacity = "0";
  mapRadarContainer.style.visibility = "hidden";
});