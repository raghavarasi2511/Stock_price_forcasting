let chart = null
let backtestChart = null

/* =========================
   MANUAL PREDICTION
========================= */

async function manualPredict(){

let ticker = document.getElementById("manual_ticker").value.trim()

let open = document.getElementById("open").value
let high = document.getElementById("high").value
let low = document.getElementById("low").value
let close = document.getElementById("close").value
let volume = document.getElementById("volume").value

if(!ticker){
alert("Please enter ticker")
return
}

if(!open || !high || !low || !close || !volume){
alert("Please enter all manual input fields")
return
}

let data = new FormData()

data.append("ticker",ticker)
data.append("open",open)
data.append("high",high)
data.append("low",low)
data.append("close",close)
data.append("volume",volume)

showLoading()

let response = await fetch("/predict_manual",{
method:"POST",
body:data
})

let result = await response.json()

displayResult(result)

/* load chart */
loadChart(ticker)

/* load backtesting */
loadBacktest(ticker)

}


/* =========================
   AUTO PREDICTION
========================= */

async function autoPredict(){

let ticker = document.getElementById("ticker").value.trim()
let date = document.getElementById("date").value

if(!ticker){
alert("Please enter ticker")
return
}

if(!date){
alert("Please select date")
return
}

let data = new FormData()

data.append("ticker",ticker)
data.append("date",date)

showLoading()

let response = await fetch("/predict_auto",{
method:"POST",
body:data
})

let result = await response.json()

displayResult(result)

/* load chart */
loadChart(ticker)

/* load backtesting */
loadBacktest(ticker)

}


/* =========================
   DISPLAY RESULT
========================= */

function displayResult(result){

if(result.error){
alert(result.error)
return
}

document.getElementById("price").innerText =
"$"+result.predicted_close

document.getElementById("change").innerText =
"Expected Next-Day Change: "+result.change+"%"

let dir = document.getElementById("direction")
let animal = document.getElementById("animal")

if(result.direction==="BULLISH"){
dir.innerHTML="<div class='bull'>⬆ Bullish Market</div>"
animal.innerHTML="<img src='/static/images/bull.gif'>"
}else{
dir.innerHTML="<div class='bear'>⬇ Bearish Market</div>"
animal.innerHTML="<img src='/static/images/bear.gif'>"
}

/* CONFIDENCE */

let confidence = result.confidence || 0
let bar = document.getElementById("confidenceBar")

bar.style.width = confidence + "%"
bar.innerText = confidence + "%"

if(confidence > 75){
bar.style.background = "#00ff9c"
}
else if(confidence > 50){
bar.style.background = "#ffc107"
}
else{
bar.style.background = "#ff4d4d"
}

}


/* =========================
   LOADING STATE
========================= */

function showLoading(){

document.getElementById("price").innerText="Loading..."
document.getElementById("change").innerText=""
document.getElementById("direction").innerHTML=""
document.getElementById("animal").innerHTML=""

}


/* =========================
   STOCK CHART
========================= */

async function loadChart(ticker){

try{

let response = await fetch("/get_chart_data?ticker="+ticker)
let result = await response.json()

if(result.error){
console.log(result.error)
return
}

let labels = result.map(d=>d.time)
let prices = result.map(d=>d.value)

let ctx = document.getElementById("stockChart").getContext("2d")

if(chart){
chart.destroy()
}

chart = new Chart(ctx,{
type:"line",
data:{
labels:labels,
datasets:[{
label:ticker+" Price",
data:prices,
borderColor:"#00ff9c",
backgroundColor:"rgba(0,255,156,0.15)",
tension:0.4,
fill:true
}]
},
options:{
responsive:true,
maintainAspectRatio:false,
plugins:{
legend:{labels:{color:"white"}}
},
scales:{
x:{ticks:{color:"white"}},
y:{ticks:{color:"white"}}
}
}
})

}catch(err){
console.log("Chart error:",err)
}

}


/* =========================
   BACKTESTING
========================= */

async function loadBacktest(ticker){

try{

let response = await fetch("/backtest?ticker="+ticker)
let result = await response.json()

console.log("BACKTEST DATA:", result) //  DEBUG

if(result.error){
console.log(result.error)
return
}

if(!result.dates || result.dates.length === 0){
console.log("No backtest data")
return
}

let labels = result.dates
let predicted = result.predictions
let actual = result.actuals

/* MAE */
document.getElementById("maeText").innerText = "MAE: " + result.mae

/* WAIT FOR CANVAS */
let canvas = document.getElementById("backtestChart")

if(!canvas){
console.log("Canvas not found")
return
}

let ctx = canvas.getContext("2d")

/* DESTROY OLD */
if(backtestChart){
backtestChart.destroy()
}

/* CREATE CHART */
backtestChart = new Chart(ctx,{
type:"line",

data:{
labels:labels,
datasets:[
{
label:"Actual Price",
data:actual,
borderColor:"#00ff9c",
backgroundColor:"rgba(0,255,156,0.1)",
tension:0.4,
fill:true
},
{
label:"Predicted Price",
data:predicted,
borderColor:"#ff4d4d",
backgroundColor:"rgba(255,77,77,0.1)",
tension:0.4,
fill:true
}
]
},

options:{
responsive:true,
maintainAspectRatio:false,

interaction:{
mode:"index",
intersect:false
},

plugins:{
legend:{
labels:{color:"white"}
}
},

scales:{
x:{
ticks:{color:"white"}
},
y:{
ticks:{color:"white"}
}
}
}

})

}catch(err){
console.log("Backtest error:",err)
}

}