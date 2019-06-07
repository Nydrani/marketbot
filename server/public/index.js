var items = {};
var item_name;
var hidden = true;

function changeGraph() {
    var type = document.querySelector('input[name="graph-type"]:checked').value;
    var scale = document.querySelector('input[name="graph-scale"]:checked').value;

    // already exists
    if (type+scale in items) {
        if (items[type+scale] != 'loading') {
            document.getElementById('img-graph').src = items[type+scale];
        }
        return;
    }

    if (!item_name) {
        return;
    }

    // show the correct graph
    if (type === "daily") {
        var i = 0;
    } else if (type === "raw") {
        var i = 1;
    }

    if (scale === "autoscaled") {
        var j = 0;
    } else if (scale === "zeroanchored") {
        var j = 1;
    }

    items[type+scale] = 'loading';
    document.getElementById('loader').style.display = "initial";
    fetch('./generate-graph?item=' + item_name + '&plot=' + i + '&scale=' + j).then((res) => {
        return res.blob();
    }).then((data) => {
        var obj = URL.createObjectURL(data);
        items[type+scale] = obj;

        // update graph
        var new_type = document.querySelector('input[name="graph-type"]:checked').value;
        var new_scale = document.querySelector('input[name="graph-scale"]:checked').value;
        if (new_type+new_scale in items && items[new_type+new_scale] != 'loading') {
            document.getElementById('img-graph').src = items[new_type+new_scale];
        }

        let graphsLoading = false;
        // show/hide loader
        for (var prop in items) {
            if (items[prop] == 'loading') {
                // dont hide
                graphsLoading = true;
                break;
            }
        }

        if (!graphsLoading) {
            document.getElementById('loader').style.display = "none";
        }

        // show stuff
        if (hidden) {
            document.getElementById('img-graph').style.display = "initial";
        }
        hidden = false;
    }).catch((err) => {
        console.log(err);
    });
}


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
    document.querySelector("#autoComplete").value = "";
    items = {};
    item_name = selection;
    changeGraph();
    //window.location.href = "./?name=" + selection;
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

