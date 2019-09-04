import * as am4core from "@amcharts/amcharts4/core";
import * as am4charts from "@amcharts/amcharts4/charts";
import am4themes_animated from "@amcharts/amcharts4/themes/animated";

import React from "react";
import { withStyles } from '@material-ui/core/styles';
import { connect } from "react-redux";
import * as _ from "lodash";
import * as moment from "moment";
import {setFilter} from "../../redux/action/simulation";
import {Grid, CircularProgress}  from '@material-ui/core';




const styles = theme => ({

    chartContainer: {
      height:'100%'
    },
    progress: {
        color: 'white',
        
    },
    grid: {
        height:'100%'
    },
    container: {
        height:'100%'
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

        window.onresize = ()=> {
            this.drawChart();
            this.props.dispatch(setFilter(null, null));
        }

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



        dateAxis.events.on("rangechangeended" ,function (event) {
            //when the chart is zoomed in, filtering will apply to simulations
            if (event.target && event.target.minZoomed) {
                let start = new Date(event.target.minZoomed)
                let end = new Date(event.target.maxZoomed)
                this.props.dispatch(setFilter(start,end));
            }

        }.bind(this));



        let valueAxis = chart.yAxes.push(new am4charts.ValueAxis());

        // Create series
        let series = chart.series.push(new am4charts.LineSeries());
        series.dataFields.valueY = "sims";
        series.dataFields.dateX = "date";
        series.strokeWidth = 2;
        series.minBulletDistance = 10;
        series.tooltipText = "{dateX} : {valueY} sims";
        series.tooltip.pointerOrientation = "vertical";
        series.tooltip.background.cornerRadius = 20;
        series.tooltip.background.fillOpacity = 0.5;
        series.tooltip.label.padding(12,12,12,12)


        // Make bullets grow on hover
        var bullet = series.bullets.push(new am4charts.CircleBullet());
        bullet.circle.strokeWidth = 2;
        bullet.circle.radius = 4;
        bullet.circle.fill = am4core.color("#fff");

        var bullethover = bullet.states.create("hover");
        bullethover.properties.scale = 1.3;

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

        let simulations = this.props.simulations;

        if (simulations && simulations.length > 0  ) {
            let sortedByCreateDT = _.sortBy(simulations, (o) => {
                return o.created;
            });


            var totalHR = Math.round((moment(sortedByCreateDT[sortedByCreateDT.length-1].created).endOf('hour') - moment(sortedByCreateDT[0].created).startOf('hour')) / 1000 / 3600);

            console.log (totalHR);

            var startHour = moment(sortedByCreateDT[0].created).startOf('hour');

            var countMap = {};

            countMap[startHour.toString()] = 0;

            for (var i=0;i<(totalHR); ++i) {
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
                    sims: countMap[simDate]
                })
            }

            
        }


        return chartData;
    }

    render() {

        const {classes} = this.props;


        if (this.state.mounted && !this.props.loading) {
            setTimeout( ()=> {
                    this.drawChart();
                }, 0);
        }

        let displayChart = this.props.loading ? "none" : "";
        let displayProgress = this.props.loading ? "" : "none";

        return (
             <div className={classes.container}>
                <div id="chartdiv" className={classes.chartContainer} style={{'display': displayChart }}/>                
                 <Grid container justify="center" alignItems="center" className = {classes.grid}  style={{'display': displayProgress }} >
                     <Grid item>
                         <CircularProgress className={classes.progress} variant="indeterminate" value='50' disableShrink={true}/>
                     </Grid>
                </Grid>
            </div>
        )
    }
}


function mapStateToProps(state) {

    return ({
      simulations: state.simulations.simulations,
      loading: state.simulations.loading
    })
  
  }
  
  export default connect(mapStateToProps)(withStyles(styles, { withTheme: true })(SimulationChart));