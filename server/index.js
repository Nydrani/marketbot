const express = require('express');
const bodyParser = require('body-parser');
const sqlite3 = require('sqlite3');
const path = require('path');
const querystring = require('querystring');
const fs = require('fs');


const app = express();
const port = 3000;

let image_num = 0


// run market script function
const runPy = function(item, save_location) {
  return new Promise(function(success, nosuccess) {
    const { spawn } = require('child_process');
    const pyprog = spawn('python3.7', ['./marketscripts.py', item, save_location], { cwd: "../" });

    pyprog.on('exit', (data) => {
      if (data == 0) {
        success();
      } else {
        nosuccess();
      }
    });
  });
}

const readFilePromise = function(file_location) {
  return new Promise(function(success, nosuccess) {
      fs.readFile(file_location, (err, data) => {
          err ? nosuccess(err) : success(data);
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
}, 1000 * 60 * 60)

app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, '/public'));


app.use(bodyParser.json());
app.use(express.static(path.join(__dirname, '/public')));

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
  console.log(item_name);

  // update image_num
  const cur_num = image_num;
  image_num++;
  image_num = image_num % 25;

  runPy(item_name, "./server/public/graphs/current" + cur_num).then(() => {
    // completed generating
    // grab image from file
    const img_name = './public/graphs/current' + cur_num + '.png'
    const img_name_zero_anchored  = './public/graphs/current' + cur_num + 'zeroanchored.png'

    return Promise.all([readFilePromise(img_name), readFilePromise(img_name_zero_anchored)]);
  }).then((args) => {
    res.render('./item.ejs', {
      image: args[0].toString('base64'),
      imagezeroanchored: args[1].toString('base64')
    });
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

