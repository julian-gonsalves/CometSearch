<!DOCTYPE html>
<html lang='en'>
<head>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <!-- The above 3 meta tags *must* come first in the head; any other head content must come *after* these tags -->
    <title>Let's go!!!</title>
    <!-- Bootstrap -->
    <link href="css/bootstrap.min.css" rel="stylesheet">
    <!-- Custom -->
    <link href="css/style.css" rel="stylesheet">
    <!-- HTML5 shim and Respond.js for IE8 support of HTML5 elements and media queries -->
    <!-- WARNING: Respond.js doesn't work if you view the page via file:// -->
    <!--[if lt IE 9]>
        <script src="https://oss.maxcdn.com/html5shiv/3.7.3/html5shiv.min.js"></script>
        <script src="https://oss.maxcdn.com/respond/1.4.2/respond.min.js"></script>
    <![endif]-->
</head>
<body>
    <nav class="navbar navbar-default navbar-fixed-top">
        <div class="container-fluid">
            <div class="navbar-header">
                <a class="navbar-brand" href="/">
                    <img alt="Comet" src="img/meteor_icon.png">
                </a>
            </div>
            <h2 class="brand-text"><a href="/"> Comet Search</a></h2>
        </div>
    </nav>
    <div class="container-fluid">
        <div class="row row-offset-mid"></div>
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
    <!-- jQuery (necessary for Bootstrap's JavaScript plugins) -->
    <script src="js/jquery.min.js"></script>
    <!-- Include all compiled plugins (below), or include individual files as needed -->
    <script src="js/bootstrap.min.js"></script>
</body>
</html>