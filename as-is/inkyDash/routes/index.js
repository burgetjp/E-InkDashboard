const routes = require('express').Router();
const request = require('request');

var bodyParser = require('body-parser')

// Tomorrow.io for Tempature
const tomorrowTempOptions = {
  method: 'GET',
  url: 'https://api.tomorrow.io/v4/weather/forecast?location=85250%20US&timesteps=1d&units=imperial&apikey=NYCH2BidiEzEUuF9ynN0YLDSi5MtESTI',
  headers: {accept: 'application/json'}
};

// NOAA for Tempature  (Testing)
const noaaTempOptions = {
  method: 'GET',
  url: 'https://api.weather.gov/gridpoints/PSR/166,61/forecast',
  headers: {
    agent: 'application/json',
    'User-Agent': 'Home Dashbaord'
  }
};

// Quotable
// https://docs.quotable.io/
const quotableOptions = {
  method: 'GET',
  url: 'https://api.quotable.io/quotes/random',
  headers: {accept: 'application/json'}
};

// Zen Quote
const zenQuoteOptions = {
  method: 'GET',
  url: 'https://zenquotes.io/api/random',
  headers: {accept: 'application/json'}
};

// Main Route for Sam's Dashboard
routes.get("/",function(req,res){

  var date_time = new Date();

  // Call tomorrow.io for tempature values
  //request(tomorrowTempOptions, function (error, response, tBody) {
    //if (error) throw new Error(error);

  // Call tomorrow.io for tempature values
  request(noaaTempOptions, function (error, response, tBody) {
    if (error) throw new Error(error);

    // Parse and define high and low temps variables
    var tempObj = JSON.parse(tBody);
    //console.log(tBody);
    var highTemp = "";
    var forecast = "";
    var precipPercent = "";
    var tempIcon = "";

    var today = new Date(date_time);

    // Get quote
    request(zenQuoteOptions, function (error, response, qBody) {
      if (error) throw new Error(error);

      var quoteObj = JSON.parse(qBody);
      // Zen Quote Format
      var quote = quoteObj[0].q;
      var author = quoteObj[0].a;
      // Quotable Format
      //var quote = quoteObj[0].content;
      //var author = quoteObj[0].author;

      var todayOr = "";
      //console.log(today.getHours())

      // NOAA
      todayOr = tempObj.properties.periods[0].name;
      highTemp = tempObj.properties.periods[0].temperature;
      forecast = tempObj.properties.periods[0].shortForecast;
      precipPercent = tempObj.properties.periods[0].probabilityOfPrecipitation.value;

      // Switch Icon based on Precipitation Percentage
      if(precipPercent < 19) {
        tempIcon = "sunny";
      }
      else if(precipPercent > 19 && precipPercent < 50 ) {
        tempIcon = "partly_cloudy_day";
      }
      else if(precipPercent > 51) {
        tempIcon = "rainy";
      }

      res.render('home', {
        day: todayOr,
        todayDate: today.toLocaleDateString(),
        todayTime: today.toLocaleTimeString(),
        highTemperature: highTemp,
        shortForecast: forecast,
        forecastIcon: tempIcon,
        fullQuote: quote,
        fullAuthor: author
      });
   });
  });

  // Backup render if API limits are hit; Can help with UI Dev.
  // res.render('home', { 
  //   todayDate: "6/26/2024",
  //   todayTime: "9:00",
  //   highTempature: "101",
  //   lowTempature: "78",
  //   fullQuote: "Testing",
  //   fullAuthor: "Testing123"
  // });
});

// Dev Route for Joe's JDU Dashboard
routes.get("/joeHome",function(req,res){

  var date_time = new Date();

  // Call tomorrow.io for tempature values
  //request(tomorrowTempOptions, function (error, response, tBody) {
    //if (error) throw new Error(error);

  // Call tomorrow.io for tempature values
  request(noaaTempOptions, function (error, response, tBody) {
    if (error) throw new Error(error);

    // Parse and define high and low temps variables
    var tempObj = JSON.parse(tBody);
    //console.log("------------> Debugging Period Issue (Line 132) : " + tBody);
    var highTemp = "";
    var forecast = "";
    var precipPercent = "";
    var tempIcon = "";

    var today = new Date(date_time);

    // Get quote
    request(zenQuoteOptions, function (error, response, qBody) {
      if (error) throw new Error(error);

      var quoteObj = JSON.parse(qBody);
      // Zen Quote Format
      var quote = quoteObj[0].q;
      var author = quoteObj[0].a;
      // Quotable Format
      //var quote = quoteObj[0].content;
      //var author = quoteObj[0].author;

      var todayOr = "";
      //console.log(today.getHours())

      // If after 3:00pm switch dashboard to show tomorrow's temps
      // Using Tomorrow.io
      // if (today.getHours() >= 15) {

      //   todayOr = "Tomorrow"
      //   highTemp = tempObj.timelines.daily[1].values.temperatureMax;
      //   lowTemp = tempObj.timelines.daily[1].values.temperatureMin;
      // } else {

      //   todayOr = "Today"
      //   highTemp = tempObj.timelines.daily[0].values.temperatureMax;
      //   lowTemp = tempObj.timelines.daily[0].values.temperatureMin;
      // }

      // Testing NOAA
      try {
        curPeriod = tempObj.properties.periods[0];
        todayOr = curPeriod.name;
        highTemp = curPeriod.temperature;
        //forecast = curPeriod.shortForecast;
        forecast = curPeriod.detailedForecast;
        precipPercent = curPeriod.probabilityOfPrecipitation.value;
      } catch(e) {
        console.log(e);
        // [Error: Uh oh!]
      }

      // Switch Icon based on Precipitation Percentage
      if(precipPercent < 19) {
        // Swtich Icon based on day or night
        if (todayOr != "Tonight") {
          tempIcon = "sunny";
        } else {
          tempIcon = "dark_mode";
        }
      }
      else if(precipPercent > 19 && precipPercent < 50 ) {
        // Swtich Icon based on day or night
        if (todayOr != "Tonight") {
          tempIcon = "partly_cloudy_day";
        } else {
          tempIcon = "partly_cloudy_night";
        }
      }
      else if(precipPercent > 51) {
        tempIcon = "rainy";
      }

      res.render('joeHome', {
        day: todayOr,
        todayDate: today.toLocaleDateString(),
        todayTime: today.toLocaleTimeString(),
        highTemperature: highTemp,
        shortForecast: forecast,
        forecastIcon: tempIcon,
        fullQuote: quote,
        fullAuthor: author
      });
   });
  });

  // Backup render if API limits are hit; Can help with UI Dev.
  // res.render('joeHome', { 
  //   todayDate: "6/26/2024",
  //   todayTime: "9:00",
  //   highTempature: "101",
  //   lowTempature: "78",
  //   fullQuote: "Testing",
  //   fullAuthor: "Testing123"
  // });
});

// Console Log the request route
routes.use(function (req,res,next) {
  console.log("Main Route: /" + req.method + " - " + req.originalUrl);
  next();
});

module.exports = routes;
