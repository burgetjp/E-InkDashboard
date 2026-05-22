const express = require('express');
const app = express();
const routes = require('./routes');
var bodyParser = require('body-parser');

require('dotenv').config();

var path = __dirname + '/views/';

// Create Application/JSON Parser
var jsonParser = bodyParser.json()
app.use(jsonParser);

// Connect all routes to app
app.use('/', routes);

// Connect statics to app
app.use("/scripts", express.static(__dirname + "/scripts/"));
app.use("/styles", express.static(__dirname + "/styles/"));
app.use("/public", express.static(__dirname + "/public/"));

// Display 404 Page
app.use("*", function(req, res){
  res.sendFile(path + "404.html")
})

app.set("view engine", "ejs")

// Assign Port
app.listen(process.env.PORT || 3000, function(){
  console.log('inkyDashboard is listening on port %d in %s mode', this.address().port, app.settings.env);
});