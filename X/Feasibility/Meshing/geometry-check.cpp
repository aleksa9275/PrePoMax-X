// Test driver for the unchanged upstream three-block mapping header.
#include "three_block_mapping.h"
#include <iostream>
#include <map>
#include <iomanip>

int main()
{
    std::vector<std::pair<std::string,bool>> checks;
    auto check=[&](const std::string& name,bool ok){ checks.push_back({name,ok}); };
    const double root3=std::sqrt(3.0);
    std::vector<three_block::Uv> uv[3]={{{0,0},{1,0},{2,0}},{{2,0},{1.5,root3/2},{1,root3}},{{1,root3},{0.5,root3/2},{0,0}}};
    std::vector<three_block::Xyz> xyz[3];
    for(int k=0;k<3;k++) for(const auto& p:uv[k]) xyz[k].push_back({p[0],p[1],0});
    const auto grid=three_block::map(uv,xyz);
    check("equilateral boundary has six nodes",grid.numberOfBoundaryNodes()==6);
    check("equilateral has three quads and one inner node",grid.quads.size()==3 && grid.innerUv.size()==1);
    check("equilateral centroid by symmetry",std::abs(grid.innerUv[0][0]-1)<1e-10 && std::abs(grid.innerUv[0][1]-root3/3)<1e-10);
    check("equilateral no folded quads",grid.numberOfFoldedQuads==0);
    check("no evaluator produces no inner XYZ",grid.innerXyz.empty());
    std::vector<three_block::Uv> nodes;
    for(int k=0;k<3;k++) for(int i=0;i<2;i++) nodes.push_back(uv[k][i]);
    nodes.insert(nodes.end(),grid.innerUv.begin(),grid.innerUv.end());
    std::map<std::pair<int,int>,int> edges;
    double area=0; bool unique=true,positive=true;
    for(const auto& quad:grid.quads){
        std::set<int> ids(quad.begin(),quad.end()); unique &= ids.size()==4;
        double twice=0;
        for(int i=0;i<4;i++){
            int a=quad[i],b=quad[(i+1)%4];
            ++edges[{std::min(a,b),std::max(a,b)}];
            twice+=nodes[a][0]*nodes[b][1]-nodes[b][0]*nodes[a][1];
        }
        positive &= twice>0; area+=twice/2;
    }
    int boundary=0,interior=0; bool manifold=true;
    for(const auto& edge:edges){boundary+=edge.second==1;interior+=edge.second==2;manifold &= edge.second==1 || edge.second==2;}
    check("quads have four distinct IDs and positive area",unique && positive);
    check("area equals independent triangle area",std::abs(area-root3)<1e-10);
    check("six boundary edges and three shared internal edges",boundary==6 && interior==3 && manifold);
    check("disk Euler characteristic",static_cast<int>(nodes.size())-static_cast<int>(edges.size())+static_cast<int>(grid.quads.size())==1);
    bool cycle=true; for(int k=0;k<3;k++) cycle &= grid.boundaryNodeId(k,2)==grid.boundaryNodeId((k+1)%3,0);
    check("boundary corners join cyclically",cycle);
    std::vector<three_block::Uv> moved[3]; std::vector<three_block::Xyz> movedXyz[3];
    for(int k=0;k<3;k++) for(const auto& p:uv[k]){moved[k].push_back({3*p[0]+7,3*p[1]-4}); movedXyz[k].push_back({3*p[0]+7,3*p[1]-4,0});}
    const auto transformed=three_block::map(moved,movedXyz);
    check("uniform scale and translation preserve topology",transformed.quads==grid.quads && transformed.numberOfFoldedQuads==0);
    check("uniform scale and translation preserve centroid",std::abs(transformed.innerUv[0][0]-10)<1e-9 && std::abs(transformed.innerUv[0][1]-(root3-4))<1e-9);
    const auto lifted=three_block::map(uv,xyz,[](const std::vector<double>& flat,std::vector<double>& out){for(size_t i=0;i<flat.size();i+=2){out.push_back(flat[i]);out.push_back(flat[i+1]);out.push_back(5);}});
    check("surface evaluator lifts interior node",lifted.innerXyz.size()==1 && std::abs(lifted.innerXyz[0][2]-5)<1e-12);
    bool rejected=false; try{three_block::map(uv,xyz,[](const std::vector<double>&,std::vector<double>& out){out.push_back(1);});}catch(const std::runtime_error&){rejected=true;}
    check("wrong evaluator length rejected",rejected);
    auto broken=xyz[0]; xyz[0].pop_back(); rejected=false;
    try{three_block::map(uv,xyz);}catch(const std::invalid_argument&){rejected=true;} xyz[0]=broken;
    check("UV XYZ side length mismatch rejected",rejected);
    int odd[3]={2,2,3}, degenerate[3]={2,2,4};
    check("odd and degenerate counts rejected",!three_block::countsValid(odd) && !three_block::countsValid(degenerate));
    // Independent exhaustive oracle: enumerate positive inner-line lengths.
    bool allCounts=true; std::vector<std::string> signatures;
    for(int a=1;a<=12;a++) for(int b=1;b<=12;b++) for(int c=1;c<=12;c++){
        int sides[3]={a,b,c}; int solution[3]={0,0,0}; bool found=false;
        for(int x=1;x<=12;x++) for(int y=1;y<=12;y++) for(int z=1;z<=12;z++)
            if(y+z==a && z+x==b && x+y==c){found=true;solution[0]=x;solution[1]=y;solution[2]=z;}
        bool valid=three_block::countsValid(sides); allCounts &= valid==found;
        std::string entry=std::to_string(a)+","+std::to_string(b)+","+std::to_string(c)+":";
        if(valid){for(int k=0;k<3;k++){allCounts &= three_block::innerLineCount(sides,k)==solution[k];entry+=(k?",":"")+std::to_string(three_block::innerLineCount(sides,k));}}
        else entry+="invalid";
        signatures.push_back(entry);
    }
    check("1728 positive count triples against independent enumeration",allCounts);
    int failures=0;for(const auto& item:checks) failures+=!item.second;
    std::cout<<std::setprecision(17)<<"{\"success\":"<<(failures?"false":"true")<<",\"passed\":"<<checks.size()-failures<<",\"failed\":"<<failures<<",\"area\":"<<area<<",\"checks\":[";
    for(size_t i=0;i<checks.size();i++){if(i)std::cout<<",";std::cout<<"{\"name\":\""<<checks[i].first<<"\",\"status\":\""<<(checks[i].second?"passed":"failed")<<"\"}";}
    std::cout<<"],\"countSignatures\":[";for(size_t i=0;i<signatures.size();i++){if(i)std::cout<<",";std::cout<<"\""<<signatures[i]<<"\"";}
    std::cout<<"]}\n";return failures?1:0;
}
