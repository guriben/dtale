import * as d3 from "d3";
import d3Tip from "d3-tip";
import _ from "lodash";
import PropTypes from "prop-types";
import React from "react";

import chartUtils from "../../chartUtils";
import { isDateCol } from "../../dtale/gridUtils";

require("./Heatmap.css");

function createHeatmap(props) {
  const { x, y, z, data, columns } = props;
  const ctx = document.getElementById("heatmap-div");
  if (!ctx || _.isEmpty(data)) {
    return;
  }
  const { offsetWidth, offsetHeight } = ctx;
  const margin = { top: 30, right: 30, bottom: 130, left: 100 },
    width = offsetWidth - margin.left - margin.right,
    height = 450 - margin.top - margin.bottom;

  const xProp = _.get(x, "value");
  const yProp = _.get(_.head(y || []), "value");
  const zProp = _.get(z, "value");

  const xGroups = _.uniq(_.get(data, "data.all.x", []));
  const yGroups = _.uniq(_.get(data, ["data", "all", yProp], []));

  d3.selectAll("svg > g > *").remove();
  $("#heatmap-div").empty();
  // append the svg object to the body of the page
  const svg = d3
    .select("#heatmap-div")
    .append("svg")
    .attr("width", width + margin.left + margin.right)
    .attr("height", height + margin.top + margin.bottom)
    .append("g")
    .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

  const area = _.size(xGroups) * _.size(yGroups);

  const xBand = d3
    .scaleBand()
    .range([0, width])
    .domain(xGroups)
    .padding(1 / area);

  let xTickFormatter = d => d;
  const isDateX = isDateCol(_.get(_.find(columns || {}, { name: xProp }), "dtype", ""));
  if (isDateX) {
    xTickFormatter = d => chartUtils.timestampLabel(d);
  }
  let xTickFilter = () => true;
  if (width / 20 < _.size(xGroups)) {
    const xFactor = Math.round(_.size(xGroups) / (width / 20));
    xTickFilter = (d, i) => {
      if (_.includes([0, _.size(xGroups) - 1], i)) {
        return true;
      }
      return i % xFactor === 0;
    };
  }
  const xAxis = svg.append("g").attr("transform", "translate(0," + height + ")");
  xAxis
    .call(
      d3
        .axisBottom(xBand)
        .tickSize(0)
        .tickFormat(xTickFormatter)
        .tickValues(xBand.domain().filter(xTickFilter))
    )
    .selectAll("text")
    .style("text-anchor", "end")
    .attr("dx", "-.8em")
    .attr("dy", ".15em")
    .attr("transform", "rotate(-65)");
  xAxis.select(".domain").attr("stroke-width", 0);

  const yBand = d3
    .scaleBand()
    .range([height, 0])
    .domain(yGroups)
    .padding(1 / area);

  let yTickFormatter = d => d;
  const isDateY = isDateCol(_.get(_.find(columns || {}, { name: yProp }), "dtype", ""));
  if (isDateY) {
    yTickFormatter = d => chartUtils.timestampLabel(d);
  }
  let yTickFilter = () => true;
  if (height / 20 < _.size(yGroups)) {
    const yFactor = Math.round(_.size(yGroups) / (height / 20));
    yTickFilter = (d, i) => {
      if (_.includes([0, _.size(yGroups) - 1], i)) {
        return true;
      }
      return i % yFactor === 0;
    };
  }
  const yAxis = svg.append("g");
  yAxis.call(
    d3
      .axisLeft(yBand)
      .tickSize(0)
      .tickFormat(yTickFormatter)
      .tickValues(yBand.domain().filter(yTickFilter))
  );
  yAxis.select(".domain").attr("stroke-width", 0);

  // alternatively colorbrewer.YlGnBu[9]
  const colors = ["#ffffd9", "#edf8b1", "#c7e9b4", "#7fcdbb", "#41b6c4", "#1d91c0", "#225ea8", "#253494", "#081d58"];

  // const myColor = d3.scaleLinear()
  //   .range(colors)
  //   .domain([data.min[zProp], data.max[zProp]]);

  const range = data.max[zProp] - data.min[zProp];
  const mid = data.min[zProp] + range / 2;
  const myColor = d3
    .scaleLinear()
    .domain([data.min[zProp], mid, data.max[zProp]])
    .range(["red", "white", "green"]);

  const heatData = _.map(_.zip(data.data.all.x, data.data.all[yProp], data.data.all[zProp]), ([x, y, value]) => ({
    x,
    y,
    value,
  }));

  const tipRenderer = d => {
    let result = `${xProp}: ${isDateX ? chartUtils.timestampLabel(d.x) : d.x}<br/>`;
    result += `${yProp}: ${isDateY ? chartUtils.timestampLabel(d.y) : d.y}<br/>`;
    result += `${zProp}: ${d.value}`;
    return result;
  };
  const tip = d3Tip()
    .attr("class", "d3-tip")
    .html(tipRenderer);
  svg.call(tip);

  const cells = svg.selectAll().data(heatData, d => `${d.x}:${d.y}`);
  cells
    .enter()
    .append("rect")
    .attr("x", d => xBand(d.x))
    .attr("y", d => yBand(d.y))
    .on("mouseover", tip.show)
    .on("mouseout", tip.hide)
    //.attr("rx", 4)
    //.attr("ry", 4)
    //.attr("class", "bordered")
    .attr("width", xBand.bandwidth())
    .attr("height", yBand.bandwidth())
    .style("fill", colors[0])
    .transition()
    .duration(1000)
    .style("fill", function(d) {
      return myColor(d.value);
    });
  cells.exit().remove();

  const legendData = [data.min[zProp]].concat(_.map(_.range(10), i => data.min[zProp] + (i + 1) * (range / 10)));
  const legend = svg
    .selectAll(".legend")
    .data(legendData, function(d) {
      return d;
    })
    .enter()
    .append("g")
    .attr("class", "legend");

  const legendElementWidth = width / (_.size(legendData) + 1);
  legend
    .append("rect")
    .attr("x", function(d, i) {
      return legendElementWidth * i;
    })
    .attr("y", height + 100)
    .attr("width", legendElementWidth)
    .attr("height", 20)
    .style("fill", function(d, i) {
      //console.log(["fill", myColor(d)])
      return myColor(d);
    });

  legend
    .append("text")
    .attr("class", "mono")
    .html(function(d) {
      return "&#8805; " + _.round(d, 2);
    })
    .attr("x", function(d, i) {
      //console.log(["x", legendElementWidth * i])
      return legendElementWidth * i;
    })
    .attr("y", height + 130);

  legend.exit().remove();
}

class Heatmap extends React.Component {
  constructor(props) {
    super(props);
  }

  componentDidMount() {
    createHeatmap(this.props);
  }

  componentDidUpdate(prevProps) {
    if (_.get(this.props, "chartType.value") !== "heatmap") {
      return;
    }
    if (!_.isEqual(this.props.data, prevProps.data)) {
      createHeatmap(this.props);
    }
  }

  render() {
    const { chartType } = this.props;
    if (chartType.value !== "heatmap") {
      return null;
    }
    return (
      <div className="row">
        <div className="col-md-12">
          <div id="heatmap-div" />
        </div>
      </div>
    );
  }
}

Heatmap.displayName = "Heatmap";
Heatmap.propTypes = {
  data: PropTypes.object, // eslint-disable-line react/no-unused-prop-types
  columns: PropTypes.arrayOf(PropTypes.object),
  x: PropTypes.object,
  y: PropTypes.arrayOf(PropTypes.object),
  z: PropTypes.object,
  group: PropTypes.arrayOf(PropTypes.object), // eslint-disable-line react/no-unused-prop-types
  chartType: PropTypes.object,
  height: PropTypes.number,
};
export default Heatmap;
