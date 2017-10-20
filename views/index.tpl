% include('header.tpl', title='Comet',userData = userData)
<div class="container-fluid">
    <div class='row'>
        <form method="GET" class="text-center">
            <div class="col-md-6 col-sm-6 col-xs-10 col-md-offset-2 col-sm-offset-2 col-xs-offset-1">
                <div class="form-group">
                    <input type="text" name="keywords" class="form-control input-lg" placeholder="type your search query here">
                </div>
            </div>
            <button type="submit" class="col-sm-2 btn btn-primary btn-lg"><span class="glyphicon glyphicon-search"></span> Search</button>
        </form> 
    </div>
    <div class="row-offset-small"></div>
    <div class="row">
        <div class="col-sm-12">
            <img src="img/meteor.png" class="img img-responsive center-block">
        </div>
    </div>
</div>
% include('footer.tpl') 