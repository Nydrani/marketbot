function changeGraph() {
  var which = document.querySelector('input[name="graph-check"]:checked').value;
  var autoscaledgraph = document.getElementById('autoscaled-graph');
  var zeroanchoredgraph = document.getElementById('zeroanchored-graph');

  // hide everyone
  zeroanchoredgraph.style.display = "none";
  autoscaledgraph.style.display = "none";

  // show the correct graph
  if (which === "autoscaled") {
    autoscaledgraph.style.display = "initial";
  } else if (which === "zeroanchored") {
    zeroanchoredgraph.style.display = "initial";
  }
}


/*
document.addEventListener("blur", event => {
  var current = event.target;
  alert(current);
  var resultsList = document.querySelector("#results_list")
  if (eventType === ") {
    resultsList.style.display = "block";
  } else {
    resultsList.style.display = "none";
  }
});
*/

new autoComplete({
  data: {
    src: async () => {
      // Loading placeholder text
      const source = await fetch("./give-me-data");
      const data = await source.json();
      // Returns Fetched data
      return data;
    },
    key: ["names"]
  },
  sort: (a, b) => {                    // Sort rendered results ascendingly | (Optional)
    if (a.match < b.match) return -1;
    if (a.match > b.match) return 1;
    return 0;
  },
  placeHolder: "Look for an item...",
  selector: "#autoComplete",
  threshold: 1,
  searchEngine: "loose",
  highlight: true,
  maxResults: 5,
  resultsList: {
    container: source => {
      resultsListID = "autoComplete_results_list";
      return resultsListID;
    },
    destination: document.querySelector("#autoComplete"),
    position: "afterend"
  },
  resultItem: (data, source) => {
    return `${data.match}`;
  },
  onSelection: feedback => {
    const selection = feedback.selection.value;
    window.location.href = "./?name=" + selection;
    // send selection to server to load image and data
  }
});

["mousedown", "keydown"].forEach(eventType => {
  const input = document.querySelector("#autoComplete");
  const resultsList = document.querySelector("#autoComplete_results_list");

  // Hide Results list when not used
  document.addEventListener(eventType, event => {
    var current = event.target;
    //console.log(current);
    if (current === input || current === resultsList || input.contains(current) || resultsList.contains(current)) {
      resultsList.style.display = "block";
    } else {
      resultsList.style.display = "none";
    }
  });
});

// initial list should be none display
document.querySelector("#autoComplete_results_list").style.display = "none";

// initial graph display
changeGraph();
