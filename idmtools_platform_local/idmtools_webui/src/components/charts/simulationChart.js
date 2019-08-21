import * as am4core from "@amcharts/amcharts4/core";
import * as am4charts from "@amcharts/amcharts4/charts";
import am4themes_animated from "@amcharts/amcharts4/themes/animated";

import React from "react";
import { withStyles } from '@material-ui/core/styles';
import { connect } from "react-redux";
import * as _ from "lodash";
import * as moment from "moment";

const styles = theme => ({

    chartContainer: {
        height:'95%'
    }

});




class SimulationChart extends React.Component {

    constructor(props) {
        super(props);
        this.generateChartData = this.generateChartData.bind(this);
        this.drawChart = this.drawChart.bind(this);
        this.state = {
            mounted : false
        }
    }

    componentDidMount() {

        this.drawChart();

        this.setState({
            mounted: true
        })
    }

    drawChart() {

        /* Chart code */
        // Themes begin
        am4core.useTheme(am4themes_animated);
        // Themes end

        // Create chart instance
        let chart = am4core.create("chartdiv", am4charts.XYChart);

        // Add data
        chart.data = this.generateChartData();

        let dateAxis = chart.xAxes.push(new am4charts.DateAxis());
        dateAxis.renderer.minGridDistance = 50;

        let valueAxis = chart.yAxes.push(new am4charts.ValueAxis());

        // Create series
        let series = chart.series.push(new am4charts.LineSeries());
        series.dataFields.valueY = "visits";
        series.dataFields.dateX = "date";
        series.strokeWidth = 2;
        series.minBulletDistance = 10;
        series.tooltipText = "{dateX} : {valueY}";
        series.tooltip.pointerOrientation = "vertical";
        series.tooltip.background.cornerRadius = 20;
        series.tooltip.background.fillOpacity = 0.5;
        series.tooltip.label.padding(12,12,12,12)

        // Add scrollbar
        chart.scrollbarX = new am4charts.XYChartScrollbar();
        chart.scrollbarX.series.push(series);

        // Add cursor
        chart.cursor = new am4charts.XYCursor();
        chart.cursor.xAxis = dateAxis;
        chart.cursor.snapToSeries = series;
    }

    generateChartData() {
        let chartData = [];

        let visits = 0;

        

        if (this.props.simulations.simulations) {
            let sortedByCreateDT = _.sortBy(this.props.simulations.simulations, (o) => {
                return o.created;
            });

            var totalHR = Math.round((moment(sortedByCreateDT[sortedByCreateDT.length-1].created) - moment(sortedByCreateDT[0].created)) / 1000 / 3600);

            console.log (totalHR);

            var startHour = moment(sortedByCreateDT[0].created).startOf('hour');

            var countMap = {};

            for (var i=0;i<totalHR; ++i) {
                countMap[startHour.add(1, 'hours').toString()] =0;
            }

            sortedByCreateDT.forEach(o=> {
                let startTime = moment(o.created).startOf('hour').toString();

                if (countMap[startTime] != null)

                    countMap[startTime] += 1 ;

            });
            
            for (var simDate in countMap) {
                chartData.push({
                    date: new Date(simDate),
                    visits: countMap[simDate]
                })
            }

            
        }


        return chartData;
    }

    render() {

        const {classes} = this.props;


        if (this.state.mounted)
            this.drawChart();

        return (
            <div id="chartdiv" className={classes.chartContainer}/>
        )
    }
}


function mapStateToProps(state) {

    return ({
      simulations: state.simulations,      
    })
  
  }
  
  export default connect(mapStateToProps)(withStyles(styles, { withTheme: true })(SimulationChart));