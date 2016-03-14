/*
 * 顶部导航条
 * title: 工具名称
 * hospitals: 所有医院的名称
 * total_items: 标注总数
 * marked_items: 已标注数目
 * hide_labeled: 是否隐藏已标注结果
 * onSelectHospital: 选择医院时触发的事件
 *
 * */
var React = require('react')
var Navbar = require("react-bootstrap/lib/Navbar")
var Nav = require('react-bootstrap/lib/Nav')
var NavItem = require('react-bootstrap/lib/NavItem')
var MenuItem = require('react-bootstrap/lib/MenuItem')
var NavDropdown = require('react-bootstrap/lib/NavDropdown')

var NavControl = React.createClass({
    onSelectHospital: function(event){
        this.props.onSelectHospital(event.target.text);
    },
    render: function(){
        var hospitalMenu = this.props.hospitals.map(function(hosp){
            return (<MenuItem eventKey={hosp} key={hosp}>{hosp}</MenuItem>);
        });
        return (  
<Navbar inverse fluid fixedTop>
    <Navbar.Header>
        <Navbar.Brand>
            <a href="#">{this.props.title}</a>
        </Navbar.Brand>
    </Navbar.Header>
    <Navbar.Collapse>
        <Nav pullRight>
            <NavItem href="#">刷新</NavItem>
            <NavItem href="#">{this.props.hide_labeled ? '显示全部' : '显示未标注'}</NavItem>
            <NavItem href="#">{this.props.total_items>0 ? '' + this.props.marked_items + '/' + this.props.total_items : ''}</NavItem>
            <NavDropdown title="医院" onSelect={this.onSelectHospital} id="basic-nav-dropdown" ref="dp_hospital">
                {hospitalMenu}
            </NavDropdown>
        </Nav>
    </Navbar.Collapse>
</Navbar>) 
    }        
}
);

module.exports = NavControl;
