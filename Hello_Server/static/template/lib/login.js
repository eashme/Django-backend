/**
 * Created by python on 18-6-26.
 */
function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

function delCookie(name)
{
var exp = new Date();
exp.setTime(exp.getTime() - 1);
var cval=getCookie(name);
if(cval!=null)
document.cookie= name + "="+cval+";expires="+exp.toGMTString();
}

function generateUUID() {
    var d = new Date().getTime();
    if (window.performance && typeof window.performance.now === "function") {
        d += performance.now(); //use high-precision timer if available
    }
    var uuid = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
        var r = (d + Math.random() * 16) % 16 | 0;
        d = Math.floor(d / 16);
        return (c == 'x' ? r : (r & 0x3 | 0x8)).toString(16);
    });
    return uuid;
}

// 生成一个图片验证码的编号，并设置页面中图片验证码img标签的src属性
function generateImageCode() {

    // 上传本次图片验证码对应的uuid:唯一区分这个图片验证码是从那个浏览器发送过来的
    var uuid = generateUUID();

    // 生成图片验证码对应的<img>标签的url
    var url = '/users/checkcode?uuid=' + uuid + '&last_uuid=' + lastUUID;

    // 将url的值赋值给<img>标签的属性
    $('#checkcode').attr('src', url);

    // 记录上一次的uuid
    lastUUID = uuid;
}

var lastUUID = '';

$(document).ready(function() {
    var errorcount = 0;

    // 登陆界面加载完毕后检查登陆状态
    $.get('/isLogin',function (request) {
        if(request.code=='0'){
            // 已登陆直接跳转到index
            location.href = 'index.html'
        }
    });

    // 生成图片验证码
    generateImageCode();
    // 将用户之前记录的用户名设置进用户名框中
    $('#user_name').val(getCookie('user_name'));


    $("#kanbuq").click(function () {
        generateImageCode();
    });

    $(".form-horizontal").submit(function () {
        return false;
    });

      $("#sub_btn").click(function () {
        var user_name = $('#user_name').val();
        var password = $('#password').val();
        var checkcode = $('#checkcode_input').val();

        if(!($('#online').prop('checked'))){
        delCookie('user_name');
        }

        params = {
            "user_name":user_name,
            "password":$.md5(password),
            "checkcode":checkcode,
            "uuid":lastUUID,
            'is_app':false
        };
        $.ajax({
              url: '/users/login',
              type: 'POST',
              data: JSON.stringify(params),
              dataType: "json",
              contentType: 'application/json',
              success: function (request) {
                // 请求成功
                if(request.code=="0"){
                  // 登陆成功
                  // 判断是否勾选了记住用户名
                    if($('#online').prop('checked')){
                        //选中了将用户输入的用户名记录在cookie中
                        $.cookie('user_name', user_name, { expires: 7 });
                    }else{
                        delCookie('user_name')
                    }
                    location.href='index.html';
                }else{
                    if(request.code=='4001'){
                        generateImageCode();
                    }
                    layer.msg(request.message,{icon:2,time:1000});
                    errorcount += 1;
                    if (errorcount>3){
                        generateImageCode();
                        errorcount = 0;
                    }
                }


              }
        });
    });


});