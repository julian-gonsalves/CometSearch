% include('header.tpl', title=search_query + ' - Comet',userData = userData)
% totalpages=0
% pagenum = 0
% setdefault('search_query', '')
<div class="container-fluid">
    <div class='row'>
        <form method="GET" class="text-center">
            <div class="col-md-6 col-sm-6 col-xs-10 col-md-offset-2 col-sm-offset-2 col-xs-offset-1">
                <div class="form-group">
                    <input type="text" name="keywords" value="{{search_query}}" class="form-control input-lg" placeholder="type your search query here">
                </div>
            </div>
            <button type="submit" class="col-sm-2 btn btn-primary btn-lg"><span class="glyphicon glyphicon-search"></span> Search</button>
        </form> 
    </div>
	<div>
	<!--Display spellchecked search query -->
		<span>Did you mean:
		
		%for i in range (0,len(spellChecked)):
			{{spellChecked[i]}}
		</span>
	</div>
    <div class='row'>
        <div class="col-md-8 col-sm-8 col-xs-10 col-md-offset-2 col-sm-offset-2 col-xs-offset-1">
            <br>
            <h2 class="text-primary">Search Results</h2>
            % if results:                
                <ul class="sync-pagination pagination-sm"></ul>
                <div id="pageContent" class="well well-sm">
                % results_list, totalpages, pagenum = results
                % for item in results_list:
                    % docid = item[0]
                    % url = item[1]
                    % title = item[2]
                    % description = item[3]
                    % rank = item[4]
                    <div class="panel panel-default">
                        <div class="panel-body">
                            <a class='text-primary' href='{{url}}'><h4>{{title}}</h4></a>
                            <small class='text-success'>{{url}}</small>
                        </div>
                    </div>
                % end
                </div>
                <ul class="sync-pagination pagination-sm"></ul>
            % else:
                <div class="alert alert-warning" role="alert">
                    <i class="glyphicon glyphicon-comment"></i> <strong>Sorry!</strong> No Links Found.
                </div>
            % end
            <h2 class="text-primary">Word Count</h2>
            <table class="table table-condensed text-center" id="results">
                <thead>
                <tr>
                    <th class="text-center">Word</th>
                    <th class="text-center">Count</th>
                </tr>
                </thead>

                <!-- Created table of keywords searched and the number of times they appeared -->
                <tbody>
                % for x in range(0,len(insertion_order_list)):
                    <tr>
                        <td>{{insertion_order_list[x]}}</td>
                        <td>{{calculated[insertion_order_list[x]]}}</td>
                        
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
                    % for (id,(word, frequency)) in enumerate(top_words, start=1):
                        <tr>
                            <td>{{id}}</td>
                            <td>{{word}}</td>
                            <td>{{int(frequency)}}</td>
                        </tr>
                    % end
                    </tbody>
                </table>
            % end

            <!-- Creates table to display top 10 recent queries -->		
            % if bool(recent_queries):
                <h2 class="text-primary">Recent Searches</h2>
                <table class="table table-condensed text-center" id="history">
                    <thead>
                    <tr>
                        <th class="text-center">#</th>
                        <th class="text-center">Word</th>
                    </tr>
                    </thead>
                    <tbody>
                    % for (id,word) in enumerate(recent_queries, start=1):
                        <tr>
                            <td>{{id}}</td>
                            <td>{{word}}</td>
                        </tr>
                    % end
                    </tbody>
                </table>
            % end
        </div>
    </div>
</div>
% include('footer.tpl',totalpages=totalpages) 
