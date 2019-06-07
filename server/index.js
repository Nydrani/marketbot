const express = require('express');
const bodyParser = require('body-parser');
const sqlite3 = require('sqlite3');
const path = require('path');
const querystring = require('querystring');
const fs = require('fs');
const randomstring = require('randomstring');


const app = express();
const port = 3000;

const db = new sqlite3.Database('../market.db', sqlite3.OPEN_READONLY);
let item_name_list = [];
non_equip_query = "SELECT item.name FROM item WHERE NOT EXISTS (SELECT * FROM equip WHERE item.id = equip.item_id)";
all_item_query = "SELECT item.name FROM item";


// run market script function
const runPy = function(item, save_location, plot_type, scale_type) {
    return new Promise(function(success, nosuccess) {
        const { spawn } = require('child_process');
        const pyprog = spawn('python3.7', ['./marketscripts.py', item, save_location, plot_type, scale_type], { cwd: "../" });

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

const clearImages = function(dir) {
    fs.readdir(dir, (err, files) => {
        files.forEach((file, index) => {
            const curPath = path.join(dir, file);
            fs.stat(curPath, (err, stat) => {
                if (err) {
                    return;
                }
                if (!stat.isFile()) {
                    return;
                }

                // 1 day cap
                const now = new Date().getTime();
                const endTime = new Date(stat.ctime).getTime() + 1000 * 60 * 60 * 24;
                if (now > endTime) {
                    fs.unlink(curPath, (err) => {});
                }
            });
        });
    });
}

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


// initial clear, and item list grab
item_name_list = grab_item_list(non_equip_query);
clearImages(path.join(__dirname, 'public', 'graphs'));
// refresh item_name_list every 1 hour
// just in case i need to clear it
const my_refresher = setInterval(function() {
    console.log("scheduled job (updating list & deleting images");
    clearImages(path.join(__dirname, 'public', 'graphs'));
    item_name_list = grab_item_list(non_equip_query);
}, 1000 * 60 * 60)



app.use(bodyParser.json());
app.use(express.static(path.join(__dirname, 'public')));

app.get('/', (req, res) => {
    const options = {
        root: __dirname
    }
    res.sendFile('./public/home.html', options);
    return;
});

app.get('/give-me-data', (req, res) => {
    // get all names from sqlite in a list
    res.send(item_name_list);
});

app.get('/generate-graph', (req, res) => {
    if (req.query.item === undefined || req.query.plot === undefined || req.query.scale === undefined) {
        const options = {
            root: __dirname
        }
        res.sendFile('./public/home.html', options);
        return;
    }
    const item = querystring.unescape(req.query.item);
    const plot = querystring.unescape(req.query.plot);
    const scale = querystring.unescape(req.query.scale);

    const rng_name = randomstring.generate(10);
    runPy(item, "./server/public/graphs/" + rng_name, plot, scale).then(() => {
        const img_name = './public/graphs/' + rng_name + '.png'
        return readFilePromise(img_name)
    }).then((data) => {
        res.send(data);
    }).catch(() => {
        // item not found
        res.status(404).send("Not found");
    });
});

app.listen(port, () => {
    console.log('Example app listening on port %s!', port);
});

