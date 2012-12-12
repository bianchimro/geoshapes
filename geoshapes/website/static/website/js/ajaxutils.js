var ajaxutils = ajaxutils || {};
ajaxutils.targetSelector =  "#ajaxutils-console-message";


ajaxutils.alertMessage = function(message, cssClass){

    var target = $(ajaxutils.targetSelector);
    var div = $("<div class='alert'><button type='button' class='close' data-dismiss='alert'>&times;</button><p>"+message+"</p></div>");
    
    if(cssClass){
        div.addClass(cssClass)
    
    }
    
    target.empty();
    target.append(div);
    

};