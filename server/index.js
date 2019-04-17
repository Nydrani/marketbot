const express = require('express');
const bodyParser = require('body-parser');
const sqlite3 = require('sqlite3');
const path = require('path');
const querystring = require('querystring');

const app = express();
const port = 3000;

const runPy = function(item, save_location) {
  return new Promise(function(success, nosuccess) {
    const { spawn } = require('child_process');
    const pyprog = spawn('python3', ['./marketscripts.py', item, save_location], { cwd: "../" });

    pyprog.on('exit', (data) => {
      if (data == 0) {
        success();
      } else {
        nosuccess();
      }
    });
  });
}

const db = new sqlite3.Database('../market.db', sqlite3.OPEN_READONLY);
let item_name_list = [];
non_equip_query = "SELECT item.name FROM item WHERE NOT EXISTS (SELECT * FROM equip WHERE item.id = equip.item_id)";
all_item_query = "SELECT item.name FROM item";
db.all(non_equip_query, [], (err, rows) => {
  if (rows) {
    rows.forEach((row) => {
      item_name_list.push(row.name);
    });
  }
}); 

app.use(bodyParser.json());
app.use(express.static(path.join(__dirname, 'public')));

app.get('/', (req, res) => {
  // if req.query is empty ( give them empty) --> otehrwise give them cool stuff
  if (req.query.name === undefined) {
    const options = {
      root: __dirname
    }
    res.sendFile('/public/home.html', options);
    return;
  }

  // generate image
  const item_name = querystring.unescape(req.query.name);
  runPy(item_name, "./server/public/graphs/current").then(() => {
    // completed generating
    const options = {
      root: __dirname
    }
    res.sendFile('/public/item.html', options);
  }).catch(() => {
    // item not found
    res.status(404).send("Not found");
  });
});

app.get('/give-me-data', (req, res) => {
  // get all names from sqlite in a list
  res.send(item_name_list);
});

app.listen(port, () => {
  console.log('Example app listening on port %s!', port);
});

