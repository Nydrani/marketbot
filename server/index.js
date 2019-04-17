const express = require('express');
const bodyParser = require('body-parser');
const sqlite3 = require('sqlite3');
const path = require('path');
const querystring = require('querystring');
const fs = require('fs');


const app = express();
const port = 3000;


// run market script function
// TODO make new image for each search
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

const grab_item_list = function(query) {
  let my_list = [];
  db.all(query, [], (err, rows) => {
    if (rows) {
      rows.forEach((row) => {
        my_list.push(row.name);
      });
    }
  }); 
  return my_list;
}

item_name_list = grab_item_list(non_equip_query);
// refresh item_name_list every 5 minutes
// just in case i need to clear it
const my_refresher = setInterval(function() {
  console.log("refreshing list");
  item_name_list = grab_item_list(non_equip_query);
}, 1000 * 60 * 10)

app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, '/public'));


app.use(bodyParser.json());
app.use(express.static(path.join(__dirname, 'public')));

app.get('/', (req, res) => {
  // if req.query is empty ( give them empty) --> otehrwise give them cool stuff
  if (req.query.name === undefined) {
    const options = {
      root: __dirname
    }
    res.sendFile('./public/home.html', options);
    return;
  }

  // generate image
  const item_name = querystring.unescape(req.query.name);
  runPy(item_name, "./server/public/graphs/current").then(() => {
    // completed generating
    // grab image from file
    const image = fs.readFileSync('./public/graphs/current.png')
    res.render('./item.ejs', { image: image.toString('base64') });
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

