/*
 * 诊断左侧候选连接
 *
 * */

var React = require('react');
var DiagListItem = React.createClass({
    onClick: function(){
        this.props.onClick(this.props.diag._id);
    },
    render: function(){
        var class_name = "list-group-item";
        if (this.props.diag.marked){
            class_name += " list-group-item-success";
            if (this.props.hide_labeled)
            {
                class_name += " hidden";
            }
        }
        return (
          <li className={class_name} onClick={this.onClick}>
              {this.props.diag._id}
          </li>
      );
    }
});

module.exports = DiagListItem;
