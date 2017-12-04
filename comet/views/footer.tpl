% setdefault('totalpages', 0) 
        <div id="errDisp"></div>
        <!-- jQuery (necessary for Bootstrap's JavaScript plugins) -->
        <script src="js/jquery.min.js"></script>
        <!-- Include all compiled plugins (below), or include individual files as needed -->
        <script src="js/bootstrap.min.js"></script>
        <script src="js/jquery.twbsPagination.min.js"></script>
        <script src="js/custom.js"></script>
        <script type="text/javascript">
        % if totalpages:
            $(function () {
                window.pagObj = $('.sync-pagination').twbsPagination({
                    totalPages: {{totalpages}},
                    visiblePages: 5,
                    onPageClick: function (event, page) {
                        $.ajax({url: "/?page="+page, 
                            success: function(result){
                                waitingDialog.hide();
                                $("#pageContent").html(result);
                            },
                            error: function( jqXHR, textStatus, errorThrown){
                                waitingDialog.hide();
                                $("#errDisp").html(errorThrown)
                            },
                            beforeSend: function(){
                                waitingDialog.show();
                            }
                        });
                    }
                }).on('page', function (event, page) {
                    //console.info(page + ' (from event listening)');
                });
            });
        % end
        </script>
    </body>
</html>