$(function() { // document ready
    $( "#year" ).text(new Date().getFullYear());
    var csrfmiddlewaretoken = $('input[name="csrfmiddlewaretoken"]').val();
    var spinner = null;
    var spinner_div = document.getElementById("result");

	$( "#example li" ).click(function( event ) {
		event.preventDefault();
        var tuple = $(this).children(":first").attr("id");
        var bname = tuple.split('-')[0];
        var aid = tuple.split('-')[1];
		$("#board_name").val(bname);
        $("#article_id").val(aid);
        $("#get_data").click();
	});
    
    $("#get_data").click(function( event ) {
		event.preventDefault();
        if (spinner == null) {
            spinner = new Spinner({color:'#000', lines: 12}).spin(spinner_div);
        } else {
            spinner.spin(spinner_div);
        }
        var bname = $("#board_name").val();
        var aid = $("#article_id").val();
        $.post(window.location.pathname, {'csrfmiddlewaretoken': csrfmiddlewaretoken, 'board_name': bname , 'article_id': aid, }, function(data) {
            $("#link").attr("href", data.link);
            $("#link").text(data.link)
            $('#result').html(JSON.stringify(data.data, null, '\t'));
        }, "json");
    });
    $("#get_data").click();
});