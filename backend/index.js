const express = require('express');
const bodyParser = require('body-parser');
const sqlite3 = require('sqlite3');

const app = express();
const port = 3000;

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

app.get('/', (req, res) => {
  const options = {
    root: __dirname
  }
  res.sendFile('index.html', options);
});

app.get('/give-me-data', (req, res) => {
  // get all names from sqlite in a list
  res.send({ names: item_name_list });
});

app.listen(port, () => {
  console.log('Example app listening on port %s!', port);
});

