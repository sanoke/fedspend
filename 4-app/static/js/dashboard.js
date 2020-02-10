/* globals Chart:false, feather:false */

(function () {
  'use strict'

  feather.replace()

  // Graphs
  var ctx = document.getElementById('myChart2')
  // eslint-disable-next-line no-unused-vars
  var myChart2 = new Chart(ctx, {
    type: 'line',
    data: {
      labels: [ {% for item in dem_totals %}
                  {{ item[1] }},
                {% endfor %}],
      datasets: [{
        label: 'Democrat'
        data: [{% for item in dem_totals %}
                  {{ item[0] }},
                {% endfor %}],
        lineTension: 0,
        backgroundColor: 'transparent',
        borderColor: '#007bff',
        borderWidth: 4,
        pointBackgroundColor: '#007bff'
      }, {
        label: 'Republican'
        data: [{% for item in repub_totals %}
                  {{ item[0] }},
               {% endfor %}],
        lineTension: 0,
        backgroundColor: 'transparent',
        borderColor: '#007bff',
        borderWidth: 4,
        pointBackgroundColor: '#007bff'
      }]
    },
    options: {
      scales: {
        yAxes: [{
          ticks: {
            beginAtZero: false
          }
        }]
      },
      legend: {
        display: false
      }
    }
  })
}())
