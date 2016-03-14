/*
 * 诊断标注右侧的候选项
 * Params:
 *  item: 候选项
 *      item.diagnosis: 这个group的标准词
 *      item.marked: 已标记
 *      item.items: 这个group的所有成员
 *
 * */
var React = require('react')
var Panel = require('react-bootstrap/lib/Panel');
var Button = require('react-bootstrap/lib/Button');

//标记候选项按钮
var MarkButton = React.createClass({
    render: function(){
        var class_name = this.props.marked ? 'hidden' : 'show';
        return (<Button bsStyle="info" bsSize='small' bsClass={class_name}>标记</Button>);        
    }
});

//已标记按钮
var MarkedButton = React.createClass({
    render: function(){
        var class_name = this.props.marked ? 'show' : 'hidden';
        return (<Button bsStyle="success" bsSize='small' bsClass={class_name}>已标记</Button>);        
    }
});

//一个诊断候选项
var DiagCandItem = React.createClass({
    render: function(){
        var button = <MarkButton marked={this.props.item.marked}></MarkButton>;
        if (this.props.item.marked){
            button = <Button bsStyle="success" bsSize='small'>已标记</Button>
        }
        else{
            button = <Button bsStyle="info" bsSize='small'>标记</Button>
        }
        var title = (<h3>
                {this.props.item.diagnosis}
                {button}
            </h3>);
        var content = this.props.item.items.map(function(text){
            return (<li key={text}><a href='#'>{text}</a></li>);
        });
       return (<Panel header={title} bsStyle='warning'><ul className="list-inline">{content}</ul></Panel>);
    }
});

module.exports = DiagCandItem;
