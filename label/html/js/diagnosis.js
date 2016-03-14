var $ = require('jquery-browserify')
var React = require('react')
var ReactDOM = require('react-dom')
var Grid = require('react-bootstrap/lib/Grid')
var Row = require('react-bootstrap/lib/Row')
var Col = require('react-bootstrap/lib/Col')
var ListGroup = require('react-bootstrap/lib/ListGroup')

var NavControl = require("./diagnosis/nav.jsx")
var api_server = "http://192.168.2.11:18001";

//医院列表
var hospitals = ['gyfyy', 'xiangya1', 'all', 'fssy', 'jsph'];
var DiagCandItem = require('./diagnosis/diagcand.jsx')

//左侧页面
//Params:
//    items: 所有待标注诊断
//    hide_labeled: 是否因此已标注的诊断
var DiagListItem = require('./diagnosis/diaglink.jsx')
var LeftSider = React.createClass({
    render: function(){
        var item_list = this.props.items.map(function(diag){
            return (<DiagListItem onClick={this.props.initGroups} diag={diag} hide_labeled={this.props.hide_labeled} key={diag._id}></DiagListItem>);
        }.bind(this));
        return (
            <ListGroup componentClass='ul'>
                {item_list}
            </ListGroup>    
        );        
    }
});

//右侧页面
//Params:
//    diag: 待标记的诊断
//State:
//      result.source: 该诊断存在于哪些医院
//      result.groups: 所有候选group
//          result.key: 即当前待标记的诊断
//          result.groups.marked: 是否已标记
//          result.groups.items: 这个group的所有成员
var RightSider = React.createClass({
    getInitialState: function(){
        return {
            source : [],
            key: '',
            groups: [],
        }                 
    },
    getCands: function(diag){
        //获取当前诊断的候选标准集合
        $.ajax({
            type: 'get',
            url: api_server + '/diagnosis/info',
            dataType: 'json',
            data: {key: diag},
            success: function(data){
                this.setState({
                    source: data.value.source,
                    key: data.value.key,
                    groups: data.value.groups,
                });
            }.bind(this),
            error: function(){
                alert('get cand fail');       
            },
        });
    },
    componentWillReceiveProps: function(next_props){
        if (next_props.diag != this.props.diag && next_props.diag){
            this.getCands(next_props.diag);
        }                           
    },
    render: function(){
        var source_list = this.state.source.map(function(source){
            return (<span key={source} className='label label-warning'>{source}</span>);
        });
        //候选项list
        var cand_list = this.state.groups.map(function(diag){
            return (<DiagCandItem key={diag._id} item={diag}></DiagCandItem>);
        });
        return (
            <div>
                <h1 className='page-header'>
                    <div id='navbar' className='navbar-collapse collapse'>
                      <ul className='nav navbar-nav'>
                          <li>  
                                <span id='curr_diagnosis'>{this.state.key}</span>
                          </li>
                          <li>
                                <small id='curr_diagnosis_info'>{source_list}</small>
                          </li>
                          <li>
                            <div className = 'navbar-form'>
                                <input type='text' className='form-control' placeholder='诊断名,为空则独立成组' id='specified_group'/>
                                <button type='button' className='btn btm-lg btn-info' id='join_group'>加入组</button>
                                <button type='button' className='btn btm-lg btn-info' id='btn_del'>删除</button>
                            </div>
                        </li>
                      </ul>
                    </div>
                </h1>
                <ul className='list-unstyled' id='cand_group_list'>{cand_list}</ul>
            </div>    
        );        
    }
});

//整个页面
var MainFrame = React.createClass(
    {
        getInitialState: function() {
            return {
                total_items : 0, 
                marked_items: 0,
                hide_labeled: false,
                items : [],
                curr_diag: '',
            };
        },
        initGroups: function(diag){
            //初始化右侧
            this.setState({curr_diag: diag});            
        },
        getDiagList: function(source){
            //获取待标注诊断列表
            $.ajax({
                url: api_server + "/diagnosis",
                dataType: 'json',
                data: {'source': source},
                success: function(data){
                    var diag_list = data.value;
                    var total_items = 0;
                    var marked_items = 0;
                    diag_list.forEach(function(item){
                        total_items += 1;
                        if (item.marked){
                            marked_items += 1;
                        }
                    });
                    this.setState({total_items: total_items, 
                        marked_items: marked_items,
                        items: data.value,
                    });
                }.bind(this),
                error: function(xhr, status, err){
                    alert('get diag list failed, ' + err.toString());
                }.bind(this),
            });
        },
        render: function(){
            return (
                <div className="container-fluid">
                {/*顶部导航*/}
                <NavControl title='诊断归一化' hospitals={this.props.hospitals} total_items={this.state.total_items} marked_items={this.state.marked_items} hide_labeled={this.state.hide_labeled} onSelectHospital={this.getDiagList}></NavControl>   
                {/*左右分两栏*/}
                <Grid fluid> 
                    <Row className='show-grid'>
                    {/*左栏*/}
                        <Col  componentClass='div' sm={3} md={2}>
                            <LeftSider initGroups={this.initGroups} items={this.state.items} hide_labeled={this.state.hide_labeled}></LeftSider>
                        </Col>
                    {/*右栏*/}
                        <Col componentClass='div' sm={9} md={10}>
                            <RightSider diag={this.state.curr_diag}></RightSider>
                        </Col>
                    </Row>
                </Grid>
                </div>
            );        
        }
    }        
);
ReactDOM.render(<MainFrame hospitals={hospitals}/>, document.getElementById('app'));
