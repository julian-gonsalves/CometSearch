<!DOCTYPE html>
<html lang='en'>
    <head>
        <meta charset="utf-8">
        <meta http-equiv="X-UA-Compatible" content="IE=edge">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <!-- The above 3 meta tags *must* come first in the head; any other head content must come *after* these tags -->
        <title>{{title}}</title>
        <!-- Bootstrap -->
        <link href="css/bootstrap.min.css" rel="stylesheet">
        <!-- Custom -->
        <link rel="icon" href="img/favicon.ico" type="image/x-icon">
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
                    <button type="button" class="navbar-toggle collapsed" data-toggle="collapse" data-target="#bs-example-navbar-collapse-1" aria-expanded="false">
                        <span class="sr-only">Toggle navigation</span>
                        <span class="icon-bar"></span>
                        <span class="icon-bar"></span>
                        <span class="icon-bar"></span>
                    </button>
                </div>
                <div class="collapse navbar-collapse" id="bs-example-navbar-collapse-1">
                    <div class="navbar-left"><h3 class="brand-text"><a href="/"> Comet Search</a></h3></div>
                    
                    % if not bool(userData):
                        <form  class="navbar-form navbar-right">
                            <a href="/?signin=Yes" class="btn btn-primary">Sign in</a>
                        </form>
                    % else:
                        % name = userData['name'] if bool(userData['name']) else userData['email']
                        <ul class="nav navbar-nav navbar-right">
                            <li><p class="navbar-text">Welcome, {{name}}</p></li>
                            <li class="active"><a href="\?signout=Yes">Sign out</a></li>
                            % if bool(userData['picture']):
                                <li class="active">\\
                                    % link = userData['link'] if bool(userData['link']) else 'javascript:void();'
                                    <a href="{{link}}" id="dp" title="Google+" target="_blank">\\
                                        % pic = userData['picture']
                                        <img src="{{pic}}" alt="Profile" width="40px" height="40px" class="img-circle img-responsive">
                                    </a>
                                </li>
                            %end
                        </ul>
                    % end
                </div>
            </div>
        </nav>
        <div class="container-fluid">
            <div class="row row-offset-mid"></div>
        </div>