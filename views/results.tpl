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
        <div class="row row-offset-small"></div>
        <div class='row'>
			<div class="col-md-8 col-sm-8 col-xs-10 col-md-offset-2 col-sm-offset-2 col-xs-offset-1">
                <div class="well">
                    <p class="text-left">Your search query was: <blockquote>{{search_query}}</blockquote></p> 
                </div>

                <h2 class="text-primary">Results</h2>
                <table class="table table-condensed text-center" id="results">
                    <thead>
                    <tr>
                        <th class="text-center">Word</th>
                        <th class="text-center">Count</th>
                    </tr>
                    </thead>

		    <!-- Created table of keywords searched and the number of times they appeared -->
                    <tbody>
                    % for x in range(0,len(insertionOrderList)):
                        <tr>
                            <td>{{insertionOrderList[x]}}</td>
                            <td>{{calculated[insertionOrderList[x]]}}</td>
                            
                        </tr>
                    % end
                    </tbody>
                </table>
                <br>
				
				
				
		<!-- Creates table to display top 20 most searched words -->		
                % if bool(top_words):
                    <h2 class="text-primary">Search History</h2>
                    <table class="table table-condensed text-center" id="history">
                        <thead>
                        <tr>
                            <th class="text-center">#</th>
                            <th class="text-center">Word</th>
                            <th class="text-center">Frequency</th>
                        </tr>
                        </thead>
                        <tbody>
                        % for (id,(word, frequency)) in zip(range(1,21),top_words):
                            <tr>
                                <td>{{id}}</td>
                                <td>{{word}}</td>
                                <td>{{frequency}}</td>
                            </tr>
                        % end
                        </tbody>
                    </table>
                % else:
                    <p>Sorry! No History</p>
                %end
            </div>
        </div>
    </div>  
	
    <!-- jQuery (necessary for Bootstrap's JavaScript plugins) -->
    <script src="js/jquery.min.js"></script>
    <!-- Include all compiled plugins (below), or include individual files as needed -->
    <script src="js/bootstrap.min.js"></script>
</body>
</html>
