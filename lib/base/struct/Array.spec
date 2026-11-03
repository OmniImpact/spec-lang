class Array{

	replace Function of Int is length(){
	}

	replace Function of Any is get(Int is index){
	}

	replace Function of null is add(Any is item){
	}

	replace Function of Any is pop(Any is default){
	}

	replace Function of Any is removeAt(Int is index, Any is default){
	}

	replace Function of Array is slice(Int is start, Int is end){
	}

	replace Function of null is clear(){
	}

	replace Function of Int is indexOf(String is search, Int is default){
	}

	Function of Boolean is isEmpty(){
		return self:length() == 0;
	}

}
